import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from copula_scengen.modules.copula.copula_sample import CopulaSample
from copula_scengen.modules.copula.copula_sample2d import CopulaSample2D
from copula_scengen.modules.copula.empirical_extension_copula2d import EmpiricalExtensionCopula2D
from copula_scengen.modules.generator.deviation_cache import DeviationCache


class CopulaSampleGenerator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: pd.DataFrame

    def generate(self, n_scenarios: int) -> CopulaSample:
        copula_sample = CopulaSample.initialize(max_rank=n_scenarios)
        for new_margin in range(1, self.data.shape[1]):
            copula_sample = self._assign_ranks_to_margin(
                copula_sample=copula_sample,
                margin=new_margin,
                n_scenarios=n_scenarios,
            )
        return copula_sample

    def _assign_ranks_to_margin(
        self,
        copula_sample: CopulaSample,
        margin: int,
        n_scenarios: int,
    ) -> CopulaSample:
        available_scenarios = list(range(n_scenarios))

        copula_samples_2d = [CopulaSample2D.initialize(n_scenarios) for i in range(margin)]
        target_copulas = [
            EmpiricalExtensionCopula2D(data=self.data.iloc[:, [prior_margin, margin]].values)
            for prior_margin in range(margin)
        ]

        new_ranks_to_assign = np.zeros_like(available_scenarios)
        for new_rank in range(1, n_scenarios + 1):
            deviation_cache: DeviationCache = DeviationCache.compute_cache(
                copula_samples=copula_samples_2d,
                target_copulas=target_copulas,
                rank=new_rank,
            )

            # Find best scenario minimizing deviation
            best_idx, best_scenario = min(
                zip(
                    available_scenarios,
                    copula_sample.retrieve_scenarios(scenario_idxs=available_scenarios),
                    strict=False,
                ),
                key=lambda item: sum(
                    deviation_cache.evaluate(margin=margin, rank=item[1][margin]) for margin in range(margin)
                ),
            )

            available_scenarios.remove(best_idx)

            copula_samples_2d = [
                copula_sample.assign(rank=rank)
                for copula_sample, rank in zip(copula_samples_2d, best_scenario, strict=False)
            ]

            new_ranks_to_assign[best_idx] = new_rank

        return copula_sample.extend(new_ranks=new_ranks_to_assign)
