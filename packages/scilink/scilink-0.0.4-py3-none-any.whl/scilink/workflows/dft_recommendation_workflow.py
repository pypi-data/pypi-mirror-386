import os
import json
import logging
from typing import Dict, Any, List, Optional

from ..agents.exp_agents.recommendation_agent import RecommendationAgent
from ..auth import get_api_key, APIKeyNotFoundError


class DFTRecommendationsWorkflow:
    """
    Standalone workflow for generating DFT recommendations from text-based analysis
    and novelty assessment results. This workflow now uses the specialized
    RecommendationAgent directly for a more explicit design.
    """

    def __init__(self,
                 google_api_key: str = None,
                 analysis_model: str = "gemini-2.5-pro-preview-06-05",
                 local_model: str = None,
                 output_dir: str = "dft_output"):

        # Auto-discover API key
        if google_api_key is None:
            google_api_key = get_api_key('google')
            if not google_api_key:
                raise APIKeyNotFoundError('google')

        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.agent = RecommendationAgent(
            google_api_key=google_api_key,
            model_name=analysis_model,
            local_model = local_model,
        )

    def run_from_files(self, analysis_file: str, novelty_file: str) -> Dict[str, Any]:
        """Generate DFT recommendations from saved files."""

        # Load files
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        with open(novelty_file, 'r') as f:
            novelty_data = json.load(f)

        # Extract data
        analysis_text = analysis_data.get("full_analysis", "")
        novel_claims = novelty_data.get("potentially_novel", [])

        return self.run_from_data(analysis_text, novel_claims)

    def run_from_data(self, analysis_text: str, novel_claims: List[str],
                      system_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate DFT recommendations from provided data."""

        # Create novelty context
        if novel_claims:
            context = "Focus on these potentially novel findings:\n"
            for i, claim in enumerate(novel_claims, 1):
                context += f"{i}. {claim}\n"
            context += "\nPrioritize DFT structures that can investigate these novel aspects."
        else:
            context = "No specific novel claims identified. Focus on most interesting aspects."

        result = self.agent.generate_dft_recommendations_from_text(
            cached_detailed_analysis=analysis_text,
            additional_prompt_context=context,
            system_info=system_info
        )

        if "error" in result:
            return {"status": "error", "message": result.get("error")}

        # Save results
        output = {
            "reasoning": result.get("analysis_summary_or_reasoning", ""),
            "recommendations": result.get("recommendations", []),
            "novel_claims": novel_claims
        }

        # Display results
        self._display_results(output["reasoning"], output["recommendations"], novel_claims)

        # Save results
        output_file = os.path.join(self.output_dir, "dft_recommendations.json")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        self.logger.info(f"Generated {len(output['recommendations'])} DFT recommendations")
        return {"status": "success", "output_file": output_file, **output}

    def _display_results(self, reasoning: str, recommendations: List[Dict], novel_claims: List[str]):
        """Display the generated DFT recommendations."""

        print("\n" + "="*60)
        print("DFT STRUCTURE RECOMMENDATIONS")
        print("="*60)

        print(f"\nNovel claims processed: {len(novel_claims)}")
        print(f"Total recommendations: {len(recommendations)}")

        print(f"\n--- Reasoning ---")
        print(reasoning)
        print("-" * 40)

        if recommendations:
            print("\n--- Recommended Structures ---")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n[{i}] Priority: {rec.get('priority', 'N/A')}")
                print(f"    {rec.get('description', 'N/A')}")
                print(f"    Justification: {rec.get('scientific_interest', 'N/A')}")
        else:
            print("\n⚠️  No recommendations generated")

        print("\n" + "="*60)
