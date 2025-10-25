"""Parliamentary debate format implementation."""

from dialectus.engine.debate_engine.types import DebatePhase
from dialectus.engine.models.providers.base_model_provider import ChatMessage

from .base import DebateFormat, FormatPhase, Position
from .topic_themes import TopicTheme, TopicTone


class ParliamentaryFormat(DebateFormat):
    """Parliamentary debate format with government and opposition."""

    @property
    def name(self) -> str:
        return "parliamentary"

    @property
    def display_name(self) -> str:
        return "Parliamentary"

    @property
    def description(self) -> str:
        return (
            "Parliamentary debate with Government and Opposition sides, formal"
            " procedures and structured speeches"
        )

    def get_phases(self, participants: list[str]) -> list[FormatPhase]:
        """Parliamentary format: PM -> LO -> Deputy PM -> Deputy LO -> Rebuttals"""
        if len(participants) < 2:
            raise ValueError("Parliamentary format requires at least 2 participants")

        # For 2 participants: Prime Minister and Leader of Opposition
        pm = participants[0]
        lo = participants[1]

        return [
            FormatPhase(
                phase=DebatePhase.OPENING,
                name="Prime Minister's Opening",
                instruction=(
                    "Deliver the Prime Minister's opening speech. Define the motion,"
                    " present the government's case, and outline key arguments while"
                    " setting the framework for the debate."
                ),
                speaking_order=[pm],
                time_multiplier=1.2,  # Slightly longer for PM
            ),
            FormatPhase(
                phase=DebatePhase.OPENING,
                name="Leader of Opposition's Response",
                instruction=(
                    "Deliver the Leader of Opposition's response. Directly challenge"
                    " the government's case while presenting an alternative framework"
                    " and counter-arguments."
                ),
                speaking_order=[lo],
                time_multiplier=1.1,
            ),
            FormatPhase(
                phase=DebatePhase.REBUTTAL,
                name="Government Rebuttal",
                instruction=(
                    "Defend government position against opposition attacks. Reinforce"
                    " key government arguments and address opposition points."
                ),
                speaking_order=[pm],
            ),
            FormatPhase(
                phase=DebatePhase.REBUTTAL,
                name="Opposition Rebuttal",
                instruction=(
                    "Final opposition response. Demolish government arguments and"
                    " consolidate opposition case."
                ),
                speaking_order=[lo],
            ),
            FormatPhase(
                phase=DebatePhase.CLOSING,
                name="Closing Statements",
                instruction=(
                    "Make final appeals to convince the House. Summarize your side's"
                    " victory in this debate."
                ),
                speaking_order=[
                    lo,
                    pm,
                ],  # Opposition closes first, government gets last word
            ),
        ]

    def get_position_assignments(self, participants: list[str]) -> dict[str, Position]:
        """First participant is Government (PRO), second is Opposition (CON)."""
        return {
            participant: Position.PRO if i == 0 else Position.CON
            for i, participant in enumerate(participants[:2])
        }

    def get_side_labels(self, participants: list[str]) -> dict[str, str]:
        """Return Parliamentary labels: Government and Opposition."""
        return {
            participant: "Government" if i == 0 else "Opposition"
            for i, participant in enumerate(participants[:2])
        }

    def get_side_descriptions(self, participants: list[str]) -> dict[str, str]:
        """Return descriptions for each side in Parliamentary debate."""
        return {
            participant: (
                "This AI will defend the government's position on the motion."
                if i == 0
                else (
                    "This AI will challenge the government's position and argue for the"
                    " opposition."
                )
            )
            for i, participant in enumerate(participants[:2])
        }

    def get_format_instructions(self) -> str:
        """Parliamentary format-specific instructions."""
        return (
            "PARLIAMENTARY DEBATE FORMAT:"
            "- Address the Speaker and fellow members respectfully"
            "- Government defends the motion, Opposition opposes it"
            "- Use parliamentary language: 'Honorable members', "
            "'The motion before the House'"
            "- Focus on policy implications and practical governance"
            "- Challenge opposing arguments while maintaining decorum"
            "Remember: You are debating in a formal parliamentary setting."
        )

    def get_max_participants(self) -> int:
        """Parliamentary can support up to 4 participants (2 per side)."""
        return 4

    def get_topic_generation_messages(
        self,
        theme: TopicTheme | None = None,
        tone: TopicTone | None = None,
    ) -> list[ChatMessage]:
        """Get Parliamentary specific messages for AI topic generation.

        Args:
            theme: Optional high-level theme to guide topic generation
            tone: Optional specific tone/sub-theme for more granular control

        Returns:
            List of message dictionaries for the AI model
        """
        # Customize system prompt for Parliamentary format
        parl_system = (
            "You are an expert at generating Parliamentary debate topics. Parliamentary"
            " debates focus on governance, policy implementation, and matters of public"
            " administration. Topics should be suitable for formal legislative"
            " discussion and policy debate."
        )

        # Build theme/tone requirements using base class helper
        theme_tone_requirements = self._build_theme_tone_requirements(theme, tone)

        # Build Parliamentary-specific user prompt
        parl_user = (
            "Generate a single Parliamentary debate topic suitable for formal policy"
            " discussion. The topic should be phrased as a motion that could be"
            f" debated in a legislature.{theme_tone_requirements} Focus on governance,"
            " policy implementation, and public administration matters. Respond with"
            " just the topic statement, no additional text or explanation."
        )

        return [
            {"role": "system", "content": parl_system},
            {"role": "user", "content": parl_user},
        ]
