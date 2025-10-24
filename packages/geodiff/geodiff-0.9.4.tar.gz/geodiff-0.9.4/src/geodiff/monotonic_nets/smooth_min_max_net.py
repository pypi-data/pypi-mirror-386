import torch
import torch.nn as nn
import torch.nn.functional as F


class SmoothMinMaxNet(nn.Module):
    """
    SmoothMinMax Monotonic Network architecture as described in [1]_ that computes a smooth
    "min of max" operation across groups of linear units, with constraints on monotonicity for each
    input dimension. Uses the LogSumExp operation for smooth min and max operations.

    Attributes
    ----------
    available_positivity_constraints : list[str]
        List of valid positivity constraints. Valid values are ['squared', 'exponential']
    input_dim : int
        Number of input features.
    n_groups : int
        Number of groups.
    nodes_per_group : int
        Number of nodes within each group.
    mono_signs : torch.Tensor
        A buffer indicating the monotonic signs for each input dimension of shape (1, 1, input_dim).
        Derived from the 'monotonicity' list.
    positivity_constraint : str
        The method used to ensure positivity of weights. E.g. squaring or exponentiating.
    raw_weights : torch.nn.Parameter
        The raw weights for the linear units of shape (n_groups, nodes_per_group, input_dim).
        These are exponentiated or left unconstrained in `forward()` based on `mono_signs`.
    biases : torch.nn.Parameter
        Bias terms for each node of shape (n_groups, nodes_per_group).
    log_beta : float
        Logarithm of the smooth maximum parameter beta. Beta calculated as exp(log_beta) ensures
        positivity of beta.
    
    Parameters
    ----------
    input_dim : int
        Number of input features.
    n_groups : int
        Number of groups.
    nodes_per_group : int
        Number of nodes within each group.
    monotonicity: list[int], optional
        List specifying monotonicity constraints for each input dimension.
        Possible values for each element:
          - 1  -> strictly increasing
          - -1 -> strictly decreasing
          - 0  -> no monotonic constraint
        If None, a list of all +1 is used (strictly increasing). The default is None.
    init_log_beta : float
        Initial value for log_beta, by default -1.
    positivity_constraint : str
        The method used to ensure positivity of weights. E.g. squaring or exponentiating.
    
    References
    ----------
    .. [1] Igel, C. (2023). Smooth min-max monotonic networks. arXiv preprint arXiv:2306.01147.
    """

    available_positivity_constraints = ['squared', 'exponential']

    def __init__(
        self,
        input_dim: int,
        n_groups: int,
        nodes_per_group: int,
        monotonicity: list = None,
        init_log_beta: float = -1.0,
        positivity_constraint: str = 'squared'
    ) -> None:
        """
        Constructs all the necessary attributes for the MinMaxNet.

        Raises
        ------
        ValueError
            If the length of `monotonicity` is not equal to `input_dim`.
        """

        super().__init__()

        self.input_dim = input_dim
        self.n_groups = n_groups
        self.nodes_per_group = nodes_per_group

        # If no monotonicity info is provided, assume increasing monotonicity for all inputs
        if monotonicity is None:
            monotonicity = [1] * input_dim
        
        if len(monotonicity) != input_dim:
            raise ValueError(
                f'Expected monotonicity to have length {input_dim}, got {len(monotonicity)}.'
            )
        
        if positivity_constraint not in self.available_positivity_constraints:
            raise ValueError(f'Invalid positivity constraint. ' \
                             f'Choose from {self.available_positivity_constraints}')
        self.positivity_constraint = positivity_constraint
        
        # Convert monotonicity from list of -1, 0, 1 to actual signs
        # We store them in a buffer so that pytorch does not treat them as parameters
        self.register_buffer(
            "mono_signs",
            torch.tensor(monotonicity, dtype = torch.float32).view(1, 1, -1)
        )
        
        # raw_weights will be exponentiated in forward() for monotonicity constraints
        self.raw_weights = nn.Parameter(
            torch.empty(n_groups, nodes_per_group, input_dim)
        )
        nn.init.trunc_normal_(self.raw_weights)

        self.biases = nn.Parameter(
            torch.zeros(n_groups, nodes_per_group)
        )
        
        # log_beta = trainable param for LSE "sharpness"
        # beta = exp(log_beta) remains positive
        self.log_beta = nn.Parameter(torch.tensor(init_log_beta, dtype = torch.float32))
    

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Performs the forward pass of the MinMaxNet.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (batch_size, input_dim).
        
        Returns
        -------
        torch.Tensor
            Output tensor of shape (batch_size, 1).
        """

        # Constrain weights according to monotonicity
        # - If monotonic sign is +1, we use exp(raw_weights) / raw_weights**2 to force positivity
        # - If monotonic sign is -1, we use -exp(raw_weights) / -raw_weights**2 to force negativity
        # - If monotonic sign is 0, we use raw_weights and leave them unconstrained
        if self.positivity_constraint == 'squared':
            w_pos = self.raw_weights ** 2
        elif self.positivity_constraint == 'exponential':
            w_pos = torch.exp(self.raw_weights)
        
        sign_matrix = torch.sign(self.mono_signs).expand_as(self.raw_weights)
        w_actual = torch.where(
            sign_matrix == 0,
            self.raw_weights,
            sign_matrix * w_pos
        )
        
        x_expanded = x.unsqueeze(1).unsqueeze(1)    # (batch_size, 1, 1, input_dim)
        w_expanded = w_actual.unsqueeze(0)          # (1, n_groups, nodes_per_group, input_dim)
        bias_expanded = self.biases.unsqueeze(0)    # (1, n_groups, nodes_per_group)

        lin = (x_expanded * w_expanded).sum(dim = -1)
        lin_out = lin + bias_expanded               # (batch_size, n_groups, nodes_per_group)

        beta = torch.exp(self.log_beta)

        # Within each group, take the max over nodes
        group_out = self._smooth_max(lin_out, beta, dim = 2)    # (batch_size, n_groups)
        # Take the min across groups
        y = -self._smooth_max(-group_out, beta, dim = 1)        # (batch_size,)
        y = y.reshape(-1, 1)

        return y


    @staticmethod
    def _smooth_max(z: torch.Tensor, beta: float, dim: int) -> None:
        r"""
        Computes a smooth approximation to the maximum function using LogSumExp function.

        The smooth maximum with parameter :math:`\beta` is defined as:

        .. math::
            \mathrm{smoothmax}_{\beta}(z) = \frac{1}{\beta} \log
                \left( \sum_i \exp \left( \beta z_i \right) \right)
        
        Parameters
        ----------
        z : torch.Tensor
            Input tensor containing values to compute maximum over.
        beta : float
            Smoothness parameter controlling approximation quality:
        dim : int
            Dimension along which to compute maximum.
        
        Returns
        -------
        torch.Tensor
            Smooth maximum values, reduced along specified dimension.
        """
        return (1.0 / beta) * torch.logsumexp(beta * z, dim = dim)