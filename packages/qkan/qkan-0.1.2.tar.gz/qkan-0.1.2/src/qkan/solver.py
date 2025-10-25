"""
QKAN layer simulating solver

This module provides a solver for quantum neural networks using PyTorch or PennyLane

Code author: Jiun-Cheng Jiang (Jim137@GitHub)
Contact: [jcjiang@phys.ntu.edu.tw](mailto:jcjiang@phys.ntu.edu.tw)
"""

import numpy as np
import torch

from .torch_qc import StateVector, TorchGates


def qml_solver(x: torch.Tensor, theta: torch.Tensor, reps: int, **kwargs):
    """
    Single-qubit data reuploading circuit using PennyLane.

    Args
    ----
        x : torch.Tensor
            shape: (batch_size, in_dim)
        theta : torch.Tensor
            shape: (reps, 2)
        reps : int
        qml_device : str
            default: "default.qubit"
    """
    import pennylane as qml  # type: ignore

    qml_device: str = kwargs.get("qml_device", "default.qubit")
    dev = qml.device(qml_device, wires=1)

    @qml.qnode(dev, interface="torch")
    def circuit(x: torch.Tensor, theta: torch.Tensor):
        """
        Args
        ----
            x : torch.Tensor
                shape: (batch_size, in_dim)
            theta : torch.Tensor
                shape: (reps, 2)
        """
        qml.RY(np.pi / 2, wires=0)
        for l in range(reps):
            qml.RZ(theta[l, 0], wires=0)
            qml.RY(theta[l, 1], wires=0)
            qml.RZ(x, wires=0)
        qml.RZ(theta[reps, 0], wires=0)
        qml.RY(theta[reps, 1], wires=0)
        return qml.expval(qml.PauliZ(0))

    return circuit(x, theta)


def torch_exact_solver(
    x: torch.Tensor,
    theta: torch.Tensor,
    preacts_weight: torch.Tensor,
    preacts_bias: torch.Tensor,
    reps: int,
    **kwargs,
) -> torch.Tensor:
    """
    Single-qubit data reuploading circuit.

    Args
    ----
        x : torch.Tensor
            shape: (batch_size, in_dim)
        theta : torch.Tensor
        preacts_weight : torch.Tensor
            shape: (out_dim, in_dim, reps)
        preacts_bias : torch.Tensor
            shape: (out_dim, in_dim, reps)
        reps : int
        ansatz : str
            options: ["pz_encoding", "px_encoding"], default: "pz_encoding"
        n_group : int
            number of neurons in a group, default: in_dim of x

    Returns
    -------
        torch.Tensor
            shape: (batch_size, out_dim, in_dim)
    """
    batch, in_dim = x.shape
    device = x.device
    ansatz = kwargs.get("ansatz", "pz_encoding")
    # group = kwargs.get("group", in_dim)
    preacts_trainable = kwargs.get("preacts_trainable", False)
    fast_measure = kwargs.get("fast_measure", True)
    out_dim = preacts_weight.shape[0]

    if preacts_trainable:
        preacts_trainable = True
        encoded_x = [
            torch.einsum("oi,bi->boi", preacts_weight[:, :, l], x).add(
                preacts_bias[:, :, l]
            )
            for l in range(reps)
        ]  # len: reps, shape: (batch_size, out_dim, in_dim)
    if len(theta.shape) != 4:
        theta = theta.unsqueeze(0)
    if theta.shape[1] != in_dim:
        repeat_out = out_dim
        repeat_in = in_dim // theta.shape[1] + 1
        theta = theta.repeat(repeat_out, repeat_in, 1, 1)[:, :in_dim, :, :]

    def pz_encoding(theta: torch.Tensor):
        """
        Args
        ----
            theta : torch.Tensor
                shape: (out_dim, n_group, reps, 2)
        """
        psi = StateVector(
            x.shape[0],
            theta.shape[0],
            theta.shape[1],
            device=device,
        )  # psi.state: torch.Tensor, shape: (batch_size, out_dim, in_dim, 2)
        psi.h()
        if not preacts_trainable:
            rug = TorchGates.rz_gate(x)
        for l in range(reps):
            psi.rz(theta[:, :, l, 0])
            psi.ry(theta[:, :, l, 1])
            if not preacts_trainable:
                psi.state = torch.einsum("mnbi,boin->boim", rug, psi.state)
            else:
                psi.state = torch.einsum(
                    "mnboi,boin->boim",
                    TorchGates.rz_gate(encoded_x[l]),
                    psi.state,
                )

        psi.rz(theta[:, :, reps, 0])
        psi.ry(theta[:, :, reps, 1])
        return psi.measure_z(fast_measure)  # shape: (batch_size, out_dim, in_dim)

    def rpz_enocding(theta: torch.Tensor):
        """
        Args
        ----
            theta : torch.Tensor
                shape: (out_dim, n_group, reps, 2)
        """
        psi = StateVector(
            x.shape[0],
            theta.shape[0],
            theta.shape[1],
            device=device,
        )
        psi.h()
        for l in range(reps):
            psi.ry(theta[:, :, l, 0])
            psi.state = torch.einsum(
                "mnboi,boin->boim",
                TorchGates.rz_gate(encoded_x[l]),
                psi.state,
            )
        psi.ry(theta[:, :, reps, 0])
        return psi.measure_z(fast_measure)  # shape: (batch_size, out_dim, in_dim)

    def px_encoding(theta: torch.Tensor):
        """
        Args
        ----
            theta: torch.Tensor
                shape: (out_dim, n_group, reps, 1)
        """
        psi = StateVector(
            x.shape[0],
            theta.shape[0],
            theta.shape[1],
            device=device,
        )  # psi.state: torch.Tensor, shape: (batch_size * g, out_dim, n_group, 2)
        psi.h()
        for l in range(reps):
            psi.rz(theta[:, :, l, 0])
            psi.state = torch.einsum(
                "mnboi,boin->boim",
                TorchGates.rx_gate(
                    torch.acos(
                        # torch.sin(
                        encoded_x[l]
                        # )
                        # add sin to prevent input from exceeding pm 1
                    )
                ),
                psi.state,
            )
            """
            # complex extension implementation
            psi.state = torch.einsum(
                "mnboi,boin->boim",
                TorchGates.acrx_gate(
                    torch.einsum("oi,bi->boi", preacts_weight[:, :, l], x)
                ),
                psi.state,
            )
            """
        psi.rz(theta[:, :, reps, 0])
        return psi.measure_z(fast_measure)  # shape: (batch_size, out_dim, in_dim)

    if ansatz == "pz_encoding":
        circuit = pz_encoding
    elif ansatz == "rpz_encoding":
        circuit = rpz_enocding
    elif ansatz == "px_encoding":
        circuit = px_encoding
    elif callable(ansatz):
        circuit = ansatz
    else:
        raise NotImplementedError()
    x = circuit(theta)  # shape: (batch_size, out_dim, in_dim)
    return x
