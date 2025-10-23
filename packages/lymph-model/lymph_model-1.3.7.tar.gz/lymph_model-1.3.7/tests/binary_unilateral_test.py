"""Test the binary unilateral system."""

import unittest
import warnings

import numpy as np

from lymph import types
from lymph.graph import LymphNodeLevel, Tumor
from lymph.modalities import Clinical

from . import fixtures

T_COL_NEW = ("tumor", "core", "t_stage")


class InitTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test the initialization of a binary model."""

    def test_value_errors(self):
        """Check that the model raises errors when the graph has issues."""
        empty_graph = {}
        only_tumor = {("tumor", "T"): []}
        only_lnl = {("lnl", "II"): []}
        duplicate_lnls = {
            ("tumor", "T"): ["II", "II"],
            ("lnl", "II"): [],
        }
        self.assertRaises(ValueError, lambda: type(self.model)(empty_graph))
        self.assertRaises(ValueError, lambda: type(self.model)(only_tumor))
        self.assertRaises(ValueError, lambda: type(self.model)(only_lnl))
        self.assertRaises(ValueError, lambda: type(self.model)(duplicate_lnls))

    def test_num_nodes(self):
        """Check number of nodes initialized."""
        num_nodes = len(self.graph_dict)
        num_tumor = len({name for kind, name in self.graph_dict if kind == "tumor"})
        num_lnls = len({name for kind, name in self.graph_dict if kind == "lnl"})

        self.assertEqual(len(self.model.graph.nodes), num_nodes)
        self.assertEqual(len(self.model.graph.tumors), num_tumor)
        self.assertEqual(len(self.model.graph.lnls), num_lnls)

    def test_num_edges(self):
        """Check number of edges initialized."""
        num_edges = sum(
            len(receiving_nodes) for receiving_nodes in self.graph_dict.values()
        )
        num_tumor_edges = sum(
            len(receiving_nodes)
            for (kind, _), receiving_nodes in self.graph_dict.items()
            if kind == "tumor"
        )
        num_lnl_edges = sum(
            len(receiving_nodes)
            for (kind, _), receiving_nodes in self.graph_dict.items()
            if kind == "lnl"
        )

        self.assertEqual(len(self.model.graph.edges), num_edges)
        self.assertEqual(len(self.model.graph.tumor_edges), num_tumor_edges)
        self.assertEqual(len(self.model.graph.lnl_edges), num_lnl_edges)
        self.assertEqual(len(self.model.graph.growth_edges), 0)

    def test_tumor(self):
        """Make sure the tumor has been initialized correctly."""
        tumor = self.model.graph.nodes["T"]
        state = tumor.state
        self.assertIsInstance(tumor, Tumor)
        self.assertListEqual(tumor.allowed_states, [state])

    def test_lnls(self):
        """Test they are all binary lymph node levels."""
        model_allowed_states = self.model.graph.allowed_states
        self.assertEqual(len(model_allowed_states), 2)

        for lnl in self.model.graph.lnls.values():
            self.assertIsInstance(lnl, LymphNodeLevel)
            self.assertTrue(lnl.is_binary)
            self.assertEqual(lnl.allowed_states, model_allowed_states)

    def test_tumor_to_lnl_edges(self):
        """Make sure the tumor to LNL edges have been initialized correctly."""
        tumor = self.model.graph.nodes["T"]
        receiving_lnls = self.graph_dict[("tumor", "T")]
        connecting_edge_names = [f"{tumor.name}_to_{lnl}" for lnl in receiving_lnls]

        for edge in self.model.graph.tumor_edges.values():
            self.assertEqual(edge.parent.name, "T")
            self.assertIn(edge.child.name, receiving_lnls)
            self.assertTrue(edge.is_tumor_spread)
            self.assertIn(edge.get_name(middle="_to_"), connecting_edge_names)


class ParameterAssignmentTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test the assignment of parameters in a binary model."""

    def test_params_assignment_via_lookup(self):
        """Make sure the spread parameters are assigned correctly."""
        params_to_set = self.create_random_params()
        edges_and_dists = self.model.graph.edges.copy()
        edges_and_dists.update(self.model.get_all_distributions())

        for param_name, value in params_to_set.items():
            name, type_ = param_name.rsplit("_", maxsplit=1)
            edges_and_dists[name].set_params(**{type_: value})
            self.assertEqual(
                edges_and_dists[name].get_params()[type_],
                value,
            )

    def test_params_assignment_via_method(self):
        """Make sure the spread parameters are assigned correctly."""
        params_to_set = self.create_random_params()
        self.model.set_params(**params_to_set)

        edges_and_dists = self.model.graph.edges.copy()
        edges_and_dists.update(self.model.get_all_distributions())

        for param_name, value in params_to_set.items():
            name, type_ = param_name.rsplit("_", maxsplit=1)
            self.assertEqual(
                edges_and_dists[name].get_params()[type_],
                value,
            )

    def test_transition_matrix_deletion(self):
        """Check if the transition matrix gets deleted when a parameter is set."""
        first_lnl_name = list(self.model.graph.lnls.values())[0].name
        trans_mat = self.model.transition_matrix()
        self.model.graph.edges[f"Tto{first_lnl_name}"].set_spread_prob(0.29579)
        self.assertFalse(np.all(trans_mat == self.model.transition_matrix()))


class TransitionMatrixTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test the generation of the transition matrix in a binary model."""

    def setUp(self):
        """Initialize a simple binary model."""
        super().setUp()
        self.model.set_params(**self.create_random_params())

    def test_shape(self):
        """Make sure the transition matrix has the correct shape."""
        num_lnls = len({name for kind, name in self.graph_dict if kind == "lnl"})
        self.assertEqual(
            self.model.transition_matrix().shape,
            (2**num_lnls, 2**num_lnls),
        )

    def test_is_probabilistic(self):
        """Make sure the rows of the transition matrix sum to one."""
        row_sums = np.sum(self.model.transition_matrix(), axis=1)
        self.assertTrue(np.allclose(row_sums, 1.0))

    @staticmethod
    def is_recusively_upper_triangular(mat: np.ndarray) -> bool:
        """Return `True` is `mat` is recursively upper triangular."""
        if mat.shape == (1, 1):
            return True

        if not np.all(np.equal(np.triu(mat), mat)):
            return False

        half = mat.shape[0] // 2
        for i in [0, 1]:
            for j in [0, 1]:
                return TransitionMatrixTestCase.is_recusively_upper_triangular(
                    mat[i * half : (i + 1) * half, j * half : (j + 1) * half],
                )  # noqa: RET503

    def test_is_recusively_upper_triangular(self) -> None:
        """Make sure the transition matrix is recursively upper triangular."""
        self.assertTrue(
            self.is_recusively_upper_triangular(self.model.transition_matrix()),
        )


class ObservationMatrixTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test the generation of the observation matrix in a binary model."""

    def setUp(self):
        """Initialize a simple binary model."""
        super().setUp()
        self.model.replace_all_modalities(fixtures.MODALITIES)

    def test_shape(self):
        """Make sure the observation matrix has the correct shape."""
        num_lnls = len(self.model.graph.lnls)
        num_modalities = len(self.model.get_all_modalities())
        expected_shape = (2**num_lnls, 2 ** (num_lnls * num_modalities))
        self.assertEqual(self.model.observation_matrix().shape, expected_shape)

    def test_is_probabilistic(self):
        """Make sure the rows of the observation matrix sum to one."""
        row_sums = np.sum(self.model.observation_matrix(), axis=1)
        self.assertTrue(np.allclose(row_sums, 1.0))


class PatientDataTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test loading the patient data."""

    def setUp(self):
        """Load patient data."""
        super().setUp()
        warnings.simplefilter("ignore", category=types.DataWarning)
        self.model.replace_all_modalities(fixtures.MODALITIES)
        self.init_diag_time_dists(early="frozen", late="parametric", foo="frozen")
        self.model.set_params(**self.create_random_params())
        self.load_patient_data(filename="2021-usz-oropharynx.csv")

    def test_load_empty_dataframe(self):
        """Make sure the patient data is loaded correctly."""
        self.model.load_patient_data(self.raw_data.iloc[:0])
        self.assertEqual(len(self.model.patient_data), 0)
        self.assertEqual(self.model.likelihood(), 0.0)

    def test_load_patient_data(self):
        """Make sure the patient data is loaded correctly."""
        self.assertEqual(len(self.model.patient_data), len(self.raw_data))

    def test_t_stages(self):
        """Make sure all T-stages are present."""
        t_stages_in_data = self.model.get_t_stages("data")
        t_stages_in_diag_time_dists = self.model.get_t_stages("distributions")
        t_stages_in_model = self.model.get_t_stages("valid")
        t_stages_intersection = set(t_stages_in_data).intersection(
            t_stages_in_diag_time_dists,
        )

        self.assertNotIn("foo", t_stages_in_model)
        self.assertEqual(len(t_stages_in_diag_time_dists), 3)
        self.assertEqual(len(t_stages_intersection), 2)
        self.assertEqual(len(t_stages_intersection), len(t_stages_in_model))

        for t_stage in t_stages_in_model:
            self.assertIn(t_stage, t_stages_in_data)
            self.assertIn(t_stage, t_stages_in_diag_time_dists)

    def test_data_matrices(self):
        """Make sure the data matrices are generated correctly."""
        for t_stage in ["early", "late"]:
            has_t_stage = self.raw_data["tumor", "1", "t_stage"].isin(
                {
                    "early": [0, 1, 2],
                    "late": [3, 4],
                }[t_stage],
            )
            data_matrix = self.model.data_matrix(t_stage).T

            self.assertEqual(
                data_matrix.shape[0],
                self.model.observation_matrix().shape[1],
            )
            self.assertEqual(
                data_matrix.shape[1],
                has_t_stage.sum(),
            )

    def test_diagnosis_matrices(self):
        """Make sure the diagnosis matrices are generated correctly."""
        for t_stage in ["early", "late"]:
            has_t_stage = self.raw_data["tumor", "1", "t_stage"].isin(
                {
                    "early": [0, 1, 2],
                    "late": [3, 4],
                }[t_stage],
            )
            diagnosis_matrix = self.model.diagnosis_matrix(t_stage).T

            self.assertEqual(
                diagnosis_matrix.shape[0],
                self.model.transition_matrix().shape[1],
            )
            self.assertEqual(
                diagnosis_matrix.shape[1],
                has_t_stage.sum(),
            )
            # some times, entries in the diagnosis matrix are almost one, but just
            # slightly larger. That's why we also have to have the `isclose` here.
            self.assertTrue(
                np.all(
                    np.isclose(diagnosis_matrix, 1.0)
                    | np.less_equal(diagnosis_matrix, 1.0),
                ),
            )

    def test_modality_replacement(self) -> None:
        """Check if the data & diagnosis matrices get updated when modalities change."""
        data_matrix = self.model.data_matrix()
        diagnosis_matrix = self.model.diagnosis_matrix()
        self.model.replace_all_modalities({"PET": Clinical(spec=0.8, sens=0.8)})
        self.assertNotEqual(
            hash(data_matrix.tobytes()),
            hash(self.model.data_matrix().tobytes()),
        )
        self.assertNotEqual(
            hash(diagnosis_matrix.tobytes()),
            hash(self.model.diagnosis_matrix().tobytes()),
        )


class LikelihoodTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test the likelihood of a model."""

    def setUp(self):
        """Load patient data."""
        super().setUp()
        self.model.replace_all_modalities(fixtures.MODALITIES)
        self.init_diag_time_dists(early="frozen", late="parametric")
        self.model.set_params(**self.create_random_params())
        self.load_patient_data(filename="2021-usz-oropharynx.csv")

    def test_log_likelihood_smaller_zero(self):
        """Make sure the log-likelihood is smaller than zero."""
        likelihood = self.model.likelihood(log=True, mode="HMM")
        self.assertLess(likelihood, 0.0)

    def test_likelihood_invalid_params_isinf(self):
        """Make sure the likelihood is `-np.inf` for invalid parameters."""
        random_params = self.create_random_params()
        for name in random_params:
            random_params[name] += 1.0
        likelihood = self.model.likelihood(
            given_params=random_params,
            log=True,
            mode="HMM",
        )
        self.assertEqual(likelihood, -np.inf)

    def test_compute_likelihood_twice(self):
        """Make sure the likelihood is the same when computed twice."""
        likelihood = self.model.likelihood(log=True, mode="HMM")
        likelihood_again = self.model.likelihood(log=True, mode="HMM")
        self.assertEqual(likelihood, likelihood_again)


class RiskTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Test anything related to the risk computation."""

    def setUp(self):
        """Load params."""
        super().setUp()
        self.model.replace_all_modalities(fixtures.MODALITIES)
        self.init_diag_time_dists(early="frozen", late="parametric")
        self.model.set_params(**self.create_random_params())

    def create_random_diagnosis(self):
        """Create a random diagnosis for each modality and LNL."""
        lnl_names = list(self.model.graph.lnls.keys())
        diagnosis = {}

        for modality in self.model.get_all_modalities():
            diagnosis[modality] = fixtures.create_random_pattern(lnl_names)

        return diagnosis

    def test_compute_encoding(self):
        """Check computation of one-hot encoding of diagnosis."""
        random_diagnosis = self.create_random_diagnosis()
        num_lnls = len(self.model.graph.lnls)
        num_mods = len(self.model.get_all_modalities())
        num_posible_diagnosis = 2 ** (num_lnls * num_mods)

        diagnosis_encoding = self.model.compute_encoding(random_diagnosis)
        self.assertEqual(diagnosis_encoding.shape, (num_posible_diagnosis,))
        self.assertEqual(diagnosis_encoding.dtype, bool)

    def test_posterior_state_dist(self):
        """Make sure the posterior state dist is correctly computed."""
        posterior_state_dist = self.model.posterior_state_dist(
            given_params=self.create_random_params(),
            given_diagnosis=self.create_random_diagnosis(),
            t_stage=self.rng.choice(["early", "late"]),
        )
        self.assertEqual(posterior_state_dist.shape, (2 ** len(self.model.graph.lnls),))
        self.assertEqual(posterior_state_dist.dtype, float)
        self.assertTrue(np.isclose(np.sum(posterior_state_dist), 1.0))

    def test_risk(self):
        """Make sure the risk is correctly computed."""
        random_pattern = fixtures.create_random_pattern(self.model.graph.lnls.keys())
        random_diagnosis = self.create_random_diagnosis()
        random_t_stage = self.rng.choice(["early", "late"])
        random_params = self.create_random_params()

        risk = self.model.risk(
            involvement=random_pattern,
            given_params=random_params,
            given_diagnosis=random_diagnosis,
            t_stage=random_t_stage,
        )
        self.assertEqual(risk.dtype, float)
        self.assertGreaterEqual(risk, 0.0)
        self.assertLessEqual(risk, 1.0)


class DataGenerationTestCase(
    fixtures.BinaryUnilateralModelMixin,
    unittest.TestCase,
):
    """Check the data generation utilities."""

    def setUp(self):
        """Load params."""
        super().setUp()
        self.model.replace_all_modalities(fixtures.MODALITIES)
        self.init_diag_time_dists(early="frozen", late="parametric")
        self.model.set_params(**self.create_random_params())

    def test_generate_early_patients(self):
        """Check that generating only early T-stage patients works."""
        early_patients = self.model.draw_patients(
            num=100,
            stage_dist=[1.0, 0.0],
            rng=self.rng,
        )
        self.assertEqual(len(early_patients), 100)
        self.assertEqual(sum(early_patients[T_COL_NEW] == "early"), 100)
        self.assertIn(("CT", "ipsi", "II"), early_patients.columns)
        self.assertIn(("FNA", "ipsi", "III"), early_patients.columns)

    def test_generate_late_patients(self):
        """Check that generating only late T-stage patients works."""
        late_patients = self.model.draw_patients(
            num=100,
            stage_dist=[0.0, 1.0],
            rng=self.rng,
        )
        self.assertEqual(len(late_patients), 100)
        self.assertEqual(sum(late_patients[T_COL_NEW] == "late"), 100)
        self.assertIn(("CT", "ipsi", "II"), late_patients.columns)
        self.assertIn(("FNA", "ipsi", "III"), late_patients.columns)

    def test_distribution_of_patients(self):
        """Check that the distribution of LNL involvement is correct."""
        # set spread params all to 0
        for lnl_edge in self.model.graph.lnl_edges.values():
            lnl_edge.set_spread_prob(0.0)

        # make all patients diagnosisd after exactly one time-step
        self.model.set_distribution("early", [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        # assign only one pathology modality
        self.model.clear_modalities()
        self.model.set_modality("tmp", spec=1.0, sens=1.0)

        # extract the tumor spread parameters
        params = self.model.get_params(as_dict=True)
        params = {
            key.replace("Tto", "").replace("_spread", ""): value
            for key, value in params.items()
            if "Tto" in key
        }

        # draw large enough amount of patients
        patients = self.model.draw_patients(
            num=10000,
            stage_dist=[1.0, 0.0],
            rng=self.rng,
        )

        # check that the distribution of LNL involvement matches tumor spread params
        for lnl, expected_mean in params.items():
            actual_mean = patients[("tmp", "ipsi", lnl)].mean()
            self.assertAlmostEqual(actual_mean, expected_mean, delta=0.02)
