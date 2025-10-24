# client.py

import argparse
import pandas as pd
import flwr as fl
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from MEDfl.rw.model import Net  # votre définition de modèle
import socket
import platform
import psutil
import shutil
import numpy as np

try:
    import GPUtil
except ImportError:
    GPUtil = None


class DPConfig:
    """
    Configuration for differential privacy.

    Attributes:
        noise_multiplier (float): Noise multiplier for DP.
        max_grad_norm (float): Maximum gradient norm for clipping.
        batch_size (int): Batch size for training.
        secure_rng (bool): Use a secure random generator.
    """

    def __init__(
        self,
        noise_multiplier: float = 1.0,
        max_grad_norm: float = 1.0,
        batch_size: int = 32,
        secure_rng: bool = False,
    ):
        self.noise_multiplier = noise_multiplier
        self.max_grad_norm = max_grad_norm
        self.batch_size = batch_size
        self.secure_rng = secure_rng


class FlowerClient(fl.client.NumPyClient):
    def __init__(
        self,
        server_address: str,
        data_path: str = "data/data.csv",
        dp_config: DPConfig = None,
        # NEW (optional client overrides; do NOT remove old args)
        val_frac: float | None = None,
        test_frac: float | None = None,
        id_col: str | None = None,
        test_ids: str | None = None,
        seed: int = 42,
    ):
        self.server_address = server_address
        self.dp_config = dp_config
        self.client_val_frac = val_frac
        self.client_test_frac = test_frac
        self.id_col = id_col
        self.test_ids = test_ids
        self.seed = seed

        # Load the CSV once; actual column selection happens on first fit using server config
        self._df = pd.read_csv(data_path)

        # Defaults used only for get_properties BEFORE first fit (last column target)
        self.feature_names = self._df.columns[:-1].tolist()
        self.target_name = self._df.columns[-1]
        self.label_counts = self._df[self.target_name].value_counts().to_dict()
        self.classes = sorted(self.label_counts.keys())

        # Tensors for metrics before first fit (fallback to all-but-last as features)
        X_default = self._df.iloc[:, :-1].values
        y_default = self._df.iloc[:, -1].values
        self.X_tensor = torch.tensor(X_default, dtype=torch.float32)
        self.y_tensor = torch.tensor(y_default, dtype=torch.float32)

        # Placeholders; we lazily build loaders/model on the first fit when we see server config
        self.train_loader: DataLoader | None = None
        self.val_loader: DataLoader | None = None
        self.test_loader: DataLoader | None = None

        self.model: Net | None = None
        self.criterion = nn.BCEWithLogitsLoss()
        self.optimizer: optim.Optimizer | None = None

        # Effective settings (filled at first fit)
        self.effective_features: list[str] = self.feature_names[:]
        self.effective_target: str = self.target_name
        self.effective_val_frac: float = float(self.client_val_frac) if self.client_val_frac is not None else 0.0
        self.effective_test_frac: float = float(self.client_test_frac) if self.client_test_frac is not None else 0.0

        self._initialized = False
        self._dp_attached = False  # to avoid wrapping twice

    # ---------- helpers

    def _mk_loader(self, X: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
        x_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32)
        return DataLoader(TensorDataset(x_t, y_t), batch_size=batch_size, shuffle=shuffle)

    def _lazy_init_from_server_config(self, config: dict):
        """
        Build model and (train, val, test) loaders once, using:
          - Server-enforced schema: config['features'] (comma-separated), config['target']
          - Split fractions: client overrides win; else use server's val_fraction/test_fraction
        """
        # ---------- schema from server (enforced if provided)
        srv_features = (config.get("features") or "").strip()
        srv_target = (config.get("target") or "").strip()
        print(f"[Client] Initializing with server schema: features='{srv_features}', target='{srv_target}'")

        if srv_target:
            if srv_target not in self._df.columns:
                raise ValueError(f"Server-specified target '{srv_target}' not in CSV columns {list(self._df.columns)}")
            target_col = srv_target
        else:
            target_col = self._df.columns[-1]  # fallback (keeps backward compatibility)

        if srv_features:
            feat_cols = [c.strip() for c in srv_features.split(",") if c.strip()]
            missing = [c for c in feat_cols if c not in self._df.columns]
            if missing:
                raise ValueError(f"Server-specified feature(s) not found in CSV: {missing}")
        else:
            feat_cols = [c for c in self._df.columns if c != target_col]

        # ---------- fractions: client overrides > server defaults > fallback (0.10/0.10)
        srv_val = config.get("val_fraction", None)
        srv_test = config.get("test_fraction", None)
        val_frac = self.client_val_frac if self.client_val_frac is not None else (float(srv_val) if srv_val is not None else 0.10)
        test_frac = self.client_test_frac if self.client_test_frac is not None else (float(srv_test) if srv_test is not None else 0.10)

        if not (0.0 <= val_frac < 1.0):
            raise ValueError(f"Invalid val_frac: {val_frac} (must be 0 <= val_frac < 1)")

        # ---------- extract arrays with the enforced schema
        X_all = self._df[feat_cols].values
        y_all = self._df[target_col].values

        # Keep tensors for global metrics logging (same behavior as before)
        self.X_tensor = torch.tensor(X_all, dtype=torch.float32)
        self.y_tensor = torch.tensor(y_all, dtype=torch.float32)

        # ---------- split
        if self.test_ids and self.test_ids.strip():  # ID-based mode
            print("[Client] Using ID-based test selection")
            test_ids_list = [i.strip() for i in self.test_ids.split(',') if i.strip()]

            if self.id_col and self.id_col in self._df.columns:
                id_series = self._df[self.id_col]
            else:
                print(f"[Client] Falling back to line numbers (index) as IDs since id_col='{self.id_col}' is invalid or not provided")
                id_series = self._df.index
                try:
                    test_ids_list = [int(i) for i in test_ids_list]
                except ValueError:
                    raise ValueError("Test IDs must be integers when using line numbers as IDs")

            test_mask = id_series.isin(test_ids_list)
            if not test_mask.any():
                print("[Client] Warning: No matching IDs found for test set; it will be empty")

            X_test = X_all[test_mask]
            y_test = y_all[test_mask]
            X_trval = X_all[~test_mask]
            y_trval = y_all[~test_mask]

            actual_test_frac = len(y_test) / len(y_all) if len(y_all) > 0 else 0.0
            if val_frac + actual_test_frac >= 1.0:
                raise ValueError(f"Validation fraction {val_frac} + actual test fraction {actual_test_frac} >= 1.0")

            self.effective_test_frac = actual_test_frac  # For logging

        else:  # Fraction-based mode (existing)
            if not (0.0 <= test_frac < 1.0 and (val_frac + test_frac) < 1.0):
                raise ValueError(f"Invalid fractions: val={val_frac}, test={test_frac} (require 0 <= val,test < 1 and val+test < 1)")

            strat_all = y_all if len(np.unique(y_all)) > 1 else None
            X_trval, X_test, y_trval, y_test = train_test_split(
                X_all, y_all, test_size=test_frac, random_state=self.seed, stratify=strat_all
            )

        # Split val from trval (common to both modes)
        if val_frac > 0 and len(y_trval) > 0:
            actual_test_frac = len(y_test) / len(y_all) if len(y_all) > 0 else 0.0
            rel_val = val_frac / (1.0 - actual_test_frac) if (1.0 - actual_test_frac) > 0 else 0.0
            strat_tr = y_trval if len(np.unique(y_trval)) > 1 else None
            X_train, X_val, y_train, y_val = train_test_split(
                X_trval, y_trval, test_size=rel_val, random_state=self.seed, stratify=strat_tr
            )
        else:
            X_train, y_train = X_trval, y_trval
            X_val, y_val = np.empty((0, X_all.shape[1])), np.empty((0,))

        # ---------- build loaders
        batch_size = self.dp_config.batch_size if self.dp_config else 32
        self.train_loader = self._mk_loader(X_train, y_train, batch_size, shuffle=True)
        self.val_loader = self._mk_loader(X_val, y_val, batch_size, shuffle=False) if len(y_val) else None
        self.test_loader = self._mk_loader(X_test, y_test, batch_size, shuffle=False)

        # ---------- model/optimizer
        input_dim = X_all.shape[1]
        self.model = Net(input_dim)
        self.optimizer = optim.SGD(self.model.parameters(), lr=0.01)

        # ---------- attach DP (same behavior as before; only wraps the train loader)
        if self.dp_config and not self._dp_attached:
            try:
                from opacus import PrivacyEngine
                privacy_engine = PrivacyEngine()
                (self.model, self.optimizer, self.train_loader) = privacy_engine.make_private(
                    module=self.model,
                    optimizer=self.optimizer,
                    data_loader=self.train_loader,
                    noise_multiplier=self.dp_config.noise_multiplier,
                    max_grad_norm=self.dp_config.max_grad_norm,
                    secure_rng=self.dp_config.secure_rng,
                )
                self._dp_attached = True
            except ImportError:
                print("Opacus non installé : exécution sans DP.")

        # ---------- record effective settings
        self.effective_features = feat_cols
        self.effective_target = target_col
        self.effective_val_frac = float(val_frac)
        # effective_test_frac already set above if ID mode; otherwise use the input
        if self.test_ids and self.test_ids.strip():
            pass  # Already set
        else:
            self.effective_test_frac = float(test_frac)

        self._initialized = True
        print(f"[Client] Initialized with features={feat_cols}, target={target_col}, val={val_frac}, test={self.effective_test_frac}")

    # ---------- FL API

    def get_parameters(self, config):
        # Ensure the model/dataloaders are built before the very first call
        if not self._initialized:
            # Use server config if provided; otherwise fall back to last-col target/all features
            try:
                self._lazy_init_from_server_config(config if isinstance(config, dict) else {})
            except Exception as e:
                # As a last resort, initialize with local defaults so Flower can proceed
                # (server-enforced schema will still be used on first fit if present)
                if not self._initialized:
                    self._lazy_init_from_server_config({})
        return [val.cpu().numpy() for val in self.model.state_dict().values()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        # Lazy init when we see the server config for the first time
        if not self._initialized:
            self._lazy_init_from_server_config(config)

        self.set_parameters(parameters)
        self.model.train()

        local_epochs = config.get("local_epochs", 5)
        total_loss = 0.0
        print(f"Training for {local_epochs} epochs...")

        for epoch in range(local_epochs):
            print(f"Epoch {epoch + 1}/{local_epochs}")
            for X_batch, y_batch in self.train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = self.criterion(outputs.squeeze(), y_batch)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item() * X_batch.size(0)

        avg_loss = total_loss / (len(self.train_loader.dataset) * local_epochs)

        # Compute metrics on FULL data (keeps your previous behavior)
        with torch.no_grad():
            logits = self.model(self.X_tensor).squeeze()
            probs = torch.sigmoid(logits).cpu().numpy()
            y_true = self.y_tensor.cpu().numpy()
        binary_preds = (probs >= 0.5).astype(int)
        try:
            auc = roc_auc_score(y_true, probs)
        except Exception:
            auc = float("nan")
        acc = accuracy_score(y_true, binary_preds)

        hostname = socket.gethostname()
        os_type = platform.system()
        metrics = {
            "hostname": hostname,
            "os_type": os_type,
            "train_loss": avg_loss,
            "train_accuracy": acc,
            "train_auc": auc,
            # Helpful for debugging/visibility
            "features": ",".join(self.effective_features),
            "target": self.effective_target,
            "val_fraction": self.effective_val_frac,
            "test_fraction": self.effective_test_frac,
        }

        return self.get_parameters(config), len(self.train_loader.dataset), metrics

    def evaluate(self, parameters, config):
        # Ensure initialized (in case server calls evaluate before fit on round 1)
        if not self._initialized:
            self._lazy_init_from_server_config(config)

        self.set_parameters(parameters)
        self.model.eval()

        # Evaluate on TEST split (not the training loader)
        total_loss = 0.0
        all_probs, all_true = [], []
        with torch.no_grad():
            for X_batch, y_batch in self.test_loader:
                outputs = self.model(X_batch)
                loss = self.criterion(outputs.squeeze(), y_batch)
                total_loss += loss.item() * X_batch.size(0)
                probs = torch.sigmoid(outputs.squeeze()).cpu().numpy()
                all_probs.extend(probs.tolist())
                all_true.extend(y_batch.cpu().numpy().tolist())

        avg_loss = total_loss / len(self.test_loader.dataset) if len(self.test_loader.dataset) > 0 else 0.0
        binary_preds = [1 if p >= 0.5 else 0 for p in all_probs]
        try:
            auc = roc_auc_score(all_true, all_probs)
        except Exception:
            auc = float("nan")
        acc = accuracy_score(all_true, binary_preds)

        metrics = {
            "eval_loss": avg_loss,
            "eval_accuracy": acc,
            "eval_auc": auc,
        }
        print(f"Evaluation metrics: {metrics}")

        return float(avg_loss), len(self.test_loader.dataset), metrics

    def get_properties(self, config):
        """
        Return dataset statistics before training starts.
        Only scalar values allowed (int, float, str, bool, bytes).
        Note: before first fit, this uses fallback (last column is target).
        """
        hostname = socket.gethostname()
        os_type = platform.system()

        # If already initialized, report the effective (server-enforced) view
        if self._initialized:
            num_samples = int(self.X_tensor.shape[0])
            num_features = int(self.X_tensor.shape[1])
            features_str = ",".join(self.effective_features)
            target_name = self.effective_target
            label_counts = pd.Series(self.y_tensor.numpy()).value_counts().to_dict()
            classes = sorted(label_counts.keys())
        else:
            num_samples = len(self.X_tensor)
            num_features = self.X_tensor.shape[1]
            features_str = ",".join(self.feature_names)
            target_name = self.target_name
            label_counts = self.label_counts
            classes = self.classes

        classes_str = ",".join(map(str, classes))
        dist_str = ",".join(f"{cls}:{cnt}" for cls, cnt in label_counts.items())

        cpu_physical = psutil.cpu_count(logical=False)
        cpu_logical = psutil.cpu_count(logical=True)
        total_mem_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        driver_present = shutil.which('nvidia-smi') is not None
        gpu_count = 0
        if GPUtil and driver_present:
            try:
                gpu_count = len(GPUtil.getGPUs())
            except Exception:
                gpu_count = 0

        return {
            "hostname": hostname,
            "os_type": os_type,
            "num_samples": num_samples,
            "num_features": num_features,
            "features": features_str,
            "target": target_name,
            "classes": classes_str,
            "label_distribution": dist_str,
            "cpu_physical_cores": cpu_physical,
            "cpu_logical_cores": cpu_logical,
            "total_memory_gb": total_mem_gb,
            "gpu_driver_present": str(driver_present),
            "gpu_count": gpu_count,
        }

    def start(self) -> None:
        """
        Start this client against its configured server_address.
        Blocks until the server shuts down.
        """
        fl.client.start_numpy_client(
            server_address=self.server_address,
            client=self,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flower client with DP support and metrics"
    )
    parser.add_argument(
        "--server_address",
        type=str,
        required=True,
        help="Adresse du serveur Flower (ex : 127.0.0.1:8080)",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="data/data.csv",
        help="Chemin vers les données CSV",
    )
    parser.add_argument(
        "--dp",
        action="store_true",
        help="Activer la confidentialité différentielle",
    )
    parser.add_argument(
        "--noise_multiplier",
        type=float,
        default=1.0,
        help="Noise multiplier pour DP",
    )
    parser.add_argument(
        "--max_grad_norm",
        type=float,
        default=1.0,
        help="Norme max pour le clipping",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Taille du batch",
    )
    # NEW — client-local optional overrides (keeps all old args intact)
    parser.add_argument(
        "--val_frac",
        type=float,
        default=None,
        help="Fraction de validation (priorité au client si fourni)",
    )
    parser.add_argument(
        "--test_frac",
        type=float,
        default=None,
        help="Fraction de test (priorité au client si fourni; ignoré si --test_ids fourni)",
    )
    parser.add_argument(
        "--id_col",
        type=str,
        default=None,
        help="Colonne des IDs pour la sélection du test (optionnel; fallback aux numéros de ligne si absent)",
    )
    parser.add_argument(
        "--test_ids",
        type=str,
        default=None,
        help="Liste d'IDs pour le test, séparés par virgule (ex: '1,3,5'; active le mode ID-based si fourni)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Graine aléatoire pour les splits",
    )

    args = parser.parse_args()

    dp_config = None
    if args.dp:
        dp_config = DPConfig(
            noise_multiplier=args.noise_multiplier,
            max_grad_norm=args.max_grad_norm,
            batch_size=args.batch_size,
        )

    client = FlowerClient(
        server_address=args.server_address,
        data_path=args.data_path,
        dp_config=dp_config,
        val_frac=args.val_frac,     # optional, overrides server if set
        test_frac=args.test_frac,   # optional, overrides server if set
        id_col=args.id_col,         # new
        test_ids=args.test_ids,     # new
        seed=args.seed,
    )
    client.start()