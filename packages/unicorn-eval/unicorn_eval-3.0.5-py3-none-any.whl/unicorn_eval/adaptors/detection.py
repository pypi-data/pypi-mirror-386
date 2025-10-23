#  Copyright 2025 Diagnostic Image Analysis Group, Radboudumc, Nijmegen, The Netherlands
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
from typing import Sequence

import numpy as np
import scipy.ndimage as ndimage
import torch
import torch.nn as nn
import torch.optim as optim
from scipy.ndimage import filters, gaussian_filter
from torch.utils.data import DataLoader, Dataset
from torch.utils.data._utils.collate import default_collate

from unicorn_eval.adaptors.base import PatchLevelTaskAdaptor
from unicorn_eval.io import INPUT_DIRECTORY, process, read_inputs


class DetectionDecoder(nn.Module):
    """MLP that maps vision encoder features to a density map."""

    def __init__(self, input_dim, hidden_dim=512, heatmap_size=16):
        super().__init__()
        self.heatmap_size = heatmap_size  # Store heatmap size
        output_size = heatmap_size * heatmap_size  # Compute output size dynamically

        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_size),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.mlp(x).view(-1, self.heatmap_size, self.heatmap_size)


class DetectionDataset(Dataset):
    """Custom dataset to load embeddings and heatmaps."""

    def __init__(self, preprocessed_data, transform=None):
        self.data = preprocessed_data
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        patch_emb, target_heatmap, patch_coordinates, case = self.data[idx]

        if self.transform:
            patch_emb = self.transform(patch_emb)
            target_heatmap = self.transform(target_heatmap)

        return patch_emb, target_heatmap, patch_coordinates, case


def custom_collate(batch):
    patch_embs, heatmaps, patch_coords, cases = zip(*batch)

    if all(hm is None for hm in heatmaps):
        heatmaps = None
    else:
        heatmaps = default_collate([hm for hm in heatmaps if hm is not None])

    return (
        default_collate(patch_embs),  # Stack patch embeddings
        heatmaps,  # Heatmaps will be None or stacked
        patch_coords,  # Keep as a list
        cases,  # Keep as a list
    )


def heatmap_to_cells_using_maxima(heatmap, neighborhood_size=5, threshold=0.01):
    """
    Detects cell centers in a heatmap using local maxima and thresholding.

    heatmap: 2D array (e.g., 32x32 or 16x16) representing the probability map.
    neighborhood_size: Size of the neighborhood for the maximum filter.
    threshold: Threshold for detecting significant cells based on local maxima.

    Returns:
    x_coords, y_coords: Coordinates of the detected cells' centers.
    """
    if isinstance(heatmap, torch.Tensor):
        heatmap = heatmap.cpu().numpy()  # Convert PyTorch tensor to NumPy array

    if heatmap.ndim != 2:
        raise ValueError(f"Expected 2D heatmap, got {heatmap.shape}")
    # Apply threshold to heatmap to create a binary map of potential cells
    maxima = heatmap > threshold

    # Use maximum filter to detect local maxima (peaks in heatmap)
    data_max = filters.maximum_filter(heatmap, neighborhood_size)
    maxima = heatmap == data_max  # Only keep true maxima

    # Apply minimum filter to identify significant local differences
    data_min = filters.minimum_filter(heatmap, neighborhood_size)
    diff = (data_max - data_min) > threshold
    maxima[diff == 0] = 0  # Keep only significant maxima

    # Label connected regions (objects) in the binary map
    labeled, num_objects = ndimage.label(maxima)
    slices = ndimage.find_objects(labeled)

    x, y = [], []

    # Get the center coordinates of each detected region (cell)
    for dy, dx in slices:
        x_center = (dx.start + dx.stop - 1) / 2  # Center of the x-axis
        y_center = (dy.start + dy.stop - 1) / 2  # Center of the y-axis
        x.append(x_center)
        y.append(y_center)

    return x, y


def train_decoder(decoder, dataloader, num_epochs=200, lr=1e-5):
    """Trains the decoder using the given data."""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    decoder.to(device)
    optimizer = optim.Adam(decoder.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    for epoch in range(num_epochs):
        total_loss = 0
        for patch_emb, target_heatmap, _, _ in dataloader:
            patch_emb = patch_emb.to(device)
            target_heatmap = target_heatmap.to(device)
            optimizer.zero_grad()
            pred_heatmap = decoder(patch_emb)
            loss = loss_fn(pred_heatmap, target_heatmap)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        logging.info(f"Epoch {epoch+1}, Loss: {total_loss / len(dataloader)}")

    return decoder


def inference(decoder, dataloader, heatmap_size=16, patch_size=224):
    """ "Run inference on the test set."""
    decoder.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        patch_predictions = []  # List to store the predictions from each patch
        patch_coordinates = []  # List to store the top-left coordinates of each patch
        roi_identifiers = []  # List to store ROI identifiers for each patch

        for patch_emb, _, patch_coordinates_batch, case in dataloader:
            patch_emb = patch_emb.to(device)

            # Make prediction for the patch
            pred_heatmap = decoder(patch_emb)

            # Store the predictions, coordinates, and ROI identifiers
            patch_predictions.append(
                pred_heatmap.cpu().squeeze(0)
            )  # Store predicted heatmap
            patch_coordinates.extend(
                patch_coordinates_batch
            )  # Store coordinates of the patch
            roi_identifiers.extend([case] * len(patch_coordinates_batch))

    case_ids = []  # List to store case identifiers
    test_predictions = []  # List to store points for each case

    for i, (patch_pred, patch_coord, case) in enumerate(
        zip(patch_predictions, patch_coordinates, roi_identifiers)
    ):
        x_local, y_local = heatmap_to_cells_using_maxima(
            patch_pred, neighborhood_size=2
        )
        patch_top_left = patch_coord

        if case not in case_ids:
            case_ids.append(case)
            test_predictions.append([])

        case_index = case_ids.index(case)
        case_points = []
        for x, y in zip(x_local, y_local):
            global_x = patch_top_left[0] + x * (
                patch_size / heatmap_size
            )  # Scaling factor: (ROI size / patch size)
            global_y = patch_top_left[1] + y * (patch_size / heatmap_size)

            case_points.append([global_x, global_y])

        test_predictions[case_index].extend(case_points)

    test_predictions = [
        np.array(case_points).tolist() for case_points in test_predictions
    ]
    return test_predictions


def assign_cells_to_patches(cell_data, patch_coordinates, patch_size):
    """Assign ROI cell coordinates to the correct patch."""
    patch_cell_map = {i: [] for i in range(len(patch_coordinates))}

    for x, y in cell_data:
        for i, (x_patch, y_patch) in enumerate(patch_coordinates):
            if (
                x_patch <= x < x_patch + patch_size
                and y_patch <= y < y_patch + patch_size
            ):
                x_local, y_local = x - x_patch, y - y_patch
                patch_cell_map[i].append((x_local, y_local))

    return patch_cell_map


def coordinates_to_heatmap(
    cell_coords, patch_size=224, heatmap_size=16, sigma: float | None = 1.0
):
    """Convert local cell coordinates into density heatmap."""
    heatmap = np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    scale = heatmap_size / patch_size

    for x, y in cell_coords:
        hm_x = int(x * scale)
        hm_y = int(y * scale)
        hm_x, hm_y = np.clip([hm_x, hm_y], 0, heatmap_size - 1)
        heatmap[hm_y, hm_x] += 1.0

    if sigma is not None:
        # ensure the output remains float32
        heatmap = gaussian_filter(heatmap, sigma=sigma).astype(np.float32)
    return heatmap


def construct_detection_labels(
    coordinates,
    embeddings,
    ids,
    labels=None,
    patch_size=224,
    heatmap_size=16,
    sigma=1.0,
    is_train=True,
):

    processed_data = []

    for case_idx, case_id in enumerate(ids):
        patch_coordinates = coordinates[case_idx]
        case_embeddings = embeddings[case_idx]

        if is_train and labels is not None:
            cell_coordinates = labels[case_idx]
            patch_cell_map = assign_cells_to_patches(
                cell_coordinates, patch_coordinates, patch_size
            )

        for i, (x_patch, y_patch) in enumerate(patch_coordinates):
            patch_emb = case_embeddings[i]

            if is_train and labels is not None:
                cell_coordinates = patch_cell_map.get(i, [])
                heatmap = coordinates_to_heatmap(
                    cell_coordinates,
                    patch_size=patch_size,
                    heatmap_size=heatmap_size,
                    sigma=sigma,
                )
            else:
                cell_coordinates = None
                heatmap = None

            processed_data.append(
                (patch_emb, heatmap, (x_patch, y_patch), f"{case_id}")
            )

    return processed_data


class DensityMap(PatchLevelTaskAdaptor):
    def __init__(
        self,
        global_patch_size=224,
        heatmap_size=16,
        num_epochs=200,
        learning_rate=1e-5,
    ):
        self.patch_size = global_patch_size
        self.heatmap_size = heatmap_size
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.decoder = None

    def fit(self, shot_features, shot_coordinates, shot_labels, shot_ids, **kwargs):
        input_dim = shot_features[0].shape[1]

        shot_data = construct_detection_labels(
            shot_coordinates,
            shot_features,
            shot_ids,
            labels=shot_labels,
            patch_size=self.patch_size,
            heatmap_size=self.heatmap_size,
        )

        dataset = DetectionDataset(preprocessed_data=shot_data)
        dataloader = DataLoader(
            dataset, batch_size=32, shuffle=True, collate_fn=custom_collate
        )

        self.decoder = DetectionDecoder(
            input_dim=input_dim, heatmap_size=self.heatmap_size
        ).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

        self.decoder = train_decoder(
            self.decoder,
            dataloader,
            num_epochs=self.num_epochs,
            lr=self.learning_rate,
        )

    def predict(self, test_cases) -> list:
        predictions = []
        for case_name in test_cases:
            test_input = process(
                read_inputs(input_dir=INPUT_DIRECTORY, case_names=[case_name])[0]
            )
            test_data = construct_detection_labels(
                [test_input["coordinates"]],
                [test_input["embeddings"]],
                [test_input["case_id"]],
                patch_size=self.patch_size,
                heatmap_size=self.heatmap_size,
                is_train=False,
            )

            test_dataset = DetectionDataset(preprocessed_data=test_data)
            test_dataloader = DataLoader(
                test_dataset, batch_size=1, shuffle=False, collate_fn=custom_collate
            )

            predicted_points = inference(
                self.decoder,
                test_dataloader,
                heatmap_size=self.heatmap_size,
                patch_size=self.patch_size,
            )
            predictions.extend(predicted_points)

        return predictions


class ConvStack(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels
        self.conv = nn.Conv2d(
            in_channels=channels,
            out_channels=channels,
            kernel_size=3,
            stride=1,
            padding=1,
            padding_mode="replicate",
        )
        self.norm = nn.GroupNorm(num_groups=1, num_channels=channels)
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.norm(x)
        x = self.activation(x)
        x = self.conv(x)
        return x


class ConvDetectionDecoder(nn.Module):

    def __init__(self, input_dim_flat: int, heatmap_size: int):
        super().__init__()
        self.heatmap_size = heatmap_size
        output_size = heatmap_size * heatmap_size
        assert (
            input_dim_flat % (heatmap_size**2) == 0
        ), f"{input_dim_flat=} needs to be divisable by {heatmap_size**2=}"
        self.spatial_dim = input_dim_flat // (heatmap_size**2)
        logging.info(f"{self.spatial_dim=}, {output_size=}, {heatmap_size=}")
        self.convs = nn.ModuleList(
            [ConvStack(channels=self.spatial_dim) for _ in range(2)]
        )
        self.conv1x1 = nn.Conv2d(
            in_channels=self.spatial_dim,
            out_channels=1,
            kernel_size=1,
        )

    def forward(self, x, for_inference: bool = True):
        out = x.view(-1, self.spatial_dim, self.heatmap_size, self.heatmap_size)
        for conv in self.convs:
            out = conv(out)
        logits = self.conv1x1(out).squeeze(1)  # [B, H, W]
        if for_inference:
            return logits.sigmoid()
        else:
            return logits


class ConvDetector(DensityMap):

    def __init__(
        self,
        patch_sizes: list[int],
    ):
        heatmap_size = 16 if len(patch_sizes) <= 2 else patch_sizes[2]
        assert patch_sizes[0] == patch_sizes[1], f"{patch_sizes[:2]=} must be square."
        assert (
            patch_sizes[0] % heatmap_size == 0
        ), f"{patch_sizes=} should be divisable by {heatmap_size=}"
        num_epochs = 200
        learning_rate = 0.00001
        super().__init__(
            patch_sizes[0],
            heatmap_size,
            num_epochs,
            learning_rate,
        )

    def fit(self, shot_features, shot_coordinates, shot_labels, shot_ids, **kwargs):
        input_dim = shot_features[0].shape[1]

        shot_data = construct_detection_labels(
            shot_coordinates,
            shot_features,
            shot_ids,
            labels=shot_labels,
            patch_size=self.patch_size,
            heatmap_size=self.heatmap_size,
            sigma=None,  # Scale heatmap values to [0, 1] for better training stability with BCEWithLogitsLoss
        )

        dataset = DetectionDataset(preprocessed_data=shot_data)
        dataloader = DataLoader(
            dataset, batch_size=32, shuffle=True, collate_fn=custom_collate
        )

        self.decoder = ConvDetectionDecoder(
            input_dim_flat=input_dim, heatmap_size=self.heatmap_size
        ).to(device := torch.device("cuda" if torch.cuda.is_available() else "cpu"))

        optimizer = optim.Adam(self.decoder.parameters(), lr=self.learning_rate)
        loss_fn = nn.BCEWithLogitsLoss()

        for epoch in range(self.num_epochs):
            total_loss = 0
            for patch_emb, target_heatmap, _, _ in dataloader:
                patch_emb = patch_emb.to(device)
                target_heatmap = target_heatmap.to(device)
                optimizer.zero_grad()
                pred_heatmap = self.decoder(patch_emb, for_inference=False)

                loss = loss_fn(pred_heatmap, target_heatmap)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            logging.info(f"Epoch {epoch+1}, Loss: {total_loss / len(dataloader)}")


class TwoLayerPerceptron(nn.Module):
    """2LP used for offline training."""

    def __init__(self, input_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, 4)  # dx, dy, dz, logit_p

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.relu(self.fc1(x)))  # [N,4]


class PatchNoduleRegressor(PatchLevelTaskAdaptor):
    """
    This class implements a lightweight MLP regression head that, for each patch:
      1. Predicts a 4-vector: [dx, dy, dz, logit_p], where (dx, dy, dz) are the predicted
         offsets from the patch center to the true nodule center in patient-space millimetres,
         and logit_p is the raw classification score.
      3. Converts patch indices to world-space coordinates via
         `compute_patch_center_3d`, then reconstructs final nodule centers by adding
         the predicted offsets to the patch center:
      3. Applies a sigmoid to logit_p to obtain a detection probability per patch.

    During inference, `infer_from_patches`:
      - Computes each patch’s world-space center.
      - Runs the MLP to get `[dx, dy, dz, logit_p]`.
      - Adds the offsets to the patch centers to get nodule coordinates.
      - Filters by a probability threshold (e.g., p > 0.9) and outputs an array of
        [x, y, z, p].
    """

    def __init__(
        self,
        hidden_dim: int = 64,
        num_epochs: int = 50,
        lr: float = 1e-3,
        shot_extra_labels: np.ndarray | None = None,
    ):
        self.hidden_dim = hidden_dim
        self.num_epochs = num_epochs
        self.lr = lr
        self.shot_extra_labels = shot_extra_labels

    def compute_patch_center_3d(self, patch_idx, spacing, origin, direction):
        """
        Convert *voxel* index of the patch centre to patient‑space millimetres.
        """
        v_mm = (np.array(patch_idx) + 0.5) * np.array(spacing)  # mm
        R = np.array(direction).reshape(3, 3)
        return np.array(origin) + R.dot(v_mm)

    def train_from_patches(
        self,
        patches: list[dict],
        hidden_dim: int = 64,
        num_epochs: int = 50,
        lr: float = 1e-3,
    ):
        """
        Train a small MLP on a flat list of patch dicts:
          each dict has feature, patch_idx, image_origin, image_spacing,
          image_direction, patch_size, patch_nodules.
        """

        feats = np.stack([p["feature"] for p in patches])  # [N, D]
        idxs = np.stack([p["patch_idx"] for p in patches])  # [N, 3]
        nods = [p["patch_nodules"] for p in patches]  # list of lists
        offsets, cls_labels = [], []
        for p, idx, nod_list in zip(patches, idxs, nods):
            origin = np.array(p["image_origin"])
            spacing = np.array(p["image_spacing"])
            direction = np.array(p["image_direction"]).reshape(3, 3)
            pc = self.compute_patch_center_3d(idx, spacing, origin, direction)
            if nod_list:
                coords = np.array(nod_list)
                nearest = coords[np.argmin(np.linalg.norm(coords - pc, axis=1))]
                delta = nearest - pc
                label = 1.0
            else:
                delta = np.zeros(3, dtype=float)
                label = 0.0
            offsets.append(delta)
            cls_labels.append(label)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        x = torch.tensor(feats, dtype=torch.float32, device=device)
        y_off = torch.tensor(np.array(offsets), dtype=torch.float32, device=device)
        y_cls = torch.tensor(np.array(cls_labels), dtype=torch.float32, device=device)
        self.model = TwoLayerPerceptron(input_dim=x.shape[1], hidden_dim=hidden_dim).to(
            device
        )
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        box_loss = nn.MSELoss()
        cls_loss = nn.BCEWithLogitsLoss()
        for _ in range(num_epochs):
            optimizer.zero_grad()
            out = self.model(x)  # [N,4]
            loss = box_loss(out[:, :3], y_off) + cls_loss(out[:, 3], y_cls)
            loss.backward()
            optimizer.step()

    @torch.no_grad()
    def infer_from_patches(self, patches: list[dict]) -> np.ndarray:
        """
        Run the trained network on patch dicts and return [x,y,z,p] per row.
        """
        device = next(self.model.parameters()).device
        feats = np.stack([p["feature"] for p in patches])
        x = torch.tensor(feats, dtype=torch.float32, device=device)
        out = self.model(x).cpu().numpy()  # [N,4]
        delta, logits = out[:, :3], out[:, 3]
        centers = np.stack(
            [
                self.compute_patch_center_3d(
                    p["patch_idx"],
                    p["image_spacing"],
                    p["image_origin"],
                    p["image_direction"],
                )
                for p in patches
            ],
            axis=0,
        )
        world_centres = centers + delta
        probs = 1 / (1 + np.exp(-logits))
        return np.concatenate([world_centres, probs[:, None]], axis=1)

    def fit(
        self,
        *,
        shot_features: list[np.ndarray],
        shot_labels: list[list[Sequence[float]]],
        shot_coordinates: list[np.ndarray],
        shot_ids: list[str],
        shot_image_origins: dict[str, Sequence[float]],
        shot_image_spacings: dict[str, Sequence[float]],
        shot_image_directions: dict[str, Sequence[float]],
        **kwargs,
    ) -> None:
        input_dim = shot_features[0].shape[1]
        self.fc1 = nn.Linear(input_dim, self.hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(self.hidden_dim, 4)

        # build a *flat* list of per-patch dicts for training
        patch_dicts: list[dict] = []
        for feats_case, idxs_case, nods_case, case_id in zip(
            shot_features,
            shot_coordinates,
            shot_labels,
            shot_ids,
        ):
            origin = shot_image_origins[case_id]
            spacing = shot_image_spacings[case_id]
            direction = shot_image_directions[case_id]
            for feat, idx in zip(feats_case, idxs_case):
                patch_dicts.append(
                    {
                        "feature": feat,
                        "patch_idx": idx,
                        "image_origin": origin,
                        "image_spacing": spacing,
                        "image_direction": direction,
                        "patch_nodules": nods_case,
                    }
                )
        self.train_from_patches(
            patches=patch_dicts,
            hidden_dim=self.hidden_dim,
            num_epochs=self.num_epochs,
            lr=self.lr,
        )

    def predict(self, test_case_ids: list[str]) -> np.ndarray:
        test_dicts: list[dict] = []
        per_patch_case_ids = []

        for case_id in test_case_ids:
            logging.info(f"Running inference for case {case_id}")
            test_input = process(
                read_inputs(input_dir=INPUT_DIRECTORY, case_names=[case_id])[0]
            )

            case_features = test_input["embeddings"]
            case_coordinates = test_input["coordinates"]

            for feat, coord in zip(case_features, case_coordinates):
                test_dicts.append(
                    {
                        "feature": feat,
                        "patch_idx": coord,
                        "image_origin": test_input["image_origin"],
                        "image_spacing": test_input["image_spacing"],
                        "image_direction": test_input["image_direction"],
                        "patch_nodules": [],  # no GT here
                    }
                )
                per_patch_case_ids.append(case_id)  # keep alignment with test_dicts

        # raw predictions [x,y,z,p] for every patch
        raw_preds = self.infer_from_patches(test_dicts)
        probs = raw_preds[:, 3]

        # ------- ONLY KEEP p > 0.9 -------- #
        mask = probs > 0.9
        raw_preds = raw_preds[mask]
        per_patch_case_ids = np.array(per_patch_case_ids, dtype=object)[mask]

        # prepend test_id to each prediction row
        rows = [[cid, *pred] for cid, pred in zip(per_patch_case_ids, raw_preds)]
        preds = np.array(rows, dtype=object)

        # Nodule count printout
        n_kept = int(mask.sum())
        logging.info(
            f"[MLPRegressor] Returning {n_kept} nodules (p > 0.9) "
            f"out of {len(mask)} patches"
        )

        return preds
