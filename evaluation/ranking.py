from __future__ import annotations

from evaluation.score import scorer


class ProviderRanking:

    def rank(
        self,
        results,
    ):

        ranked = []

        for result in results:

            score = scorer.score(
                result
            )

            ranked.append(
                (
                    score,
                    result,
                )
            )

        ranked.sort(
            reverse=True,
            key=lambda x: x[0],
        )

        return ranked


ranking = ProviderRanking()