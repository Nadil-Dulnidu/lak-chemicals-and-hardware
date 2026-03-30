from app.configs.logging import get_logger

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage

from app.core.agents.agents import (
    get_clarification_validation_agent,
    get_user_confirmation_agent,
    get_product_intelligence_agent,
    get_product_suggestion_agent,
    get_add_to_cart_agent,
    get_analytics_quiry_validation_agent,
    get_analytics_router_agent,
    get_inventory_analytics_agent,
    get_product_performance_agent,
    get_sales_analytics_agent,
    get_sales_prediction_agent,
)
from app.core.graph.state import GraphState
from app.core.graph.graph_builder import GraphBuilder


# Configure logging
logger = get_logger(__name__)


class GraphExecuter:
    """
    Singleton class to ensure only one compiled graph instance exists.

    This ensures that the graph is compiled only once and reused across
    the application, improving performance and memory efficiency.
    """

    _instance = None
    _compiled_graph = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_graph(self, checkpointer=None):
        """
        Get the compiled graph instance. Creates it if it doesn't exist.

        Args:
            checkpointer: Optional checkpointer for state persistence.
                         Defaults to InMemorySaver if not provided.
                         Note: This is only used on first initialization.

        Returns:
            Compiled StateGraph ready for execution.
        """
        if self._compiled_graph is None:
            self._compiled_graph = self._create_graph(checkpointer)
        return self._compiled_graph

    def _create_graph(self, checkpointer=None):
        """
        Internal method to create the interview coach graph.

        This function:
        1. Initializes the requirement gathering agent
        2. Initializes the interview strategist agent
        3. Creates a graph builder with dependencies
        4. Builds and returns the compiled graph

        Args:
            checkpointer: Optional checkpointer for state persistence.
                         Defaults to InMemorySaver if not provided.

        Returns:
            Compiled StateGraph ready for execution.
        """
        logger.info("Creating Interview Coach graph (singleton)...")

        # Initialize dependencies
        clarification_validation_agent = get_clarification_validation_agent()
        user_confirmation_agent = get_user_confirmation_agent()
        product_intelligence_agent = get_product_intelligence_agent()
        product_suggestion_agent = get_product_suggestion_agent()
        add_to_cart_agent = get_add_to_cart_agent()
        analytics_query_validation_agent = get_analytics_quiry_validation_agent()
        analytics_router_agent = get_analytics_router_agent()
        inventory_analytics_agent = get_inventory_analytics_agent()
        product_performance_agent = get_product_performance_agent()
        sales_analytics_agent = get_sales_analytics_agent()
        sales_prediction_agent = get_sales_prediction_agent()
        checkpointer = checkpointer or InMemorySaver()

        # Build the graph
        builder = GraphBuilder(
            clarification_validation_agent=clarification_validation_agent,
            product_intelligence_agent=product_intelligence_agent,
            product_suggestion_agent=product_suggestion_agent,
            user_confirmation_agent=user_confirmation_agent,
            add_to_cart_agent=add_to_cart_agent,
            analytics_query_validation_agent=analytics_query_validation_agent,
            analytics_router_agent=analytics_router_agent,
            inventory_analytics_agent=inventory_analytics_agent,
            product_performance_agent=product_performance_agent,
            sales_analytics_agent=sales_analytics_agent,
            sales_prediction_agent=sales_prediction_agent,
            checkpointer=checkpointer,
        )

        compiled_graph = builder.build()
        logger.info("Graph created successfully")

        return compiled_graph

    @classmethod
    def reset(cls):
        """
        Reset the singleton instance. Useful for testing.
        """
        cls._instance = None
        if cls._instance:
            cls._instance._compiled_graph = None


def get_compiled_graph(checkpointer=None):
    """
    Get the singleton compiled graph instance.

    Args:
        checkpointer: Optional checkpointer for state persistence.
                     Defaults to InMemorySaver if not provided.
                     Note: This is only used on first initialization.

    Returns:
        Compiled StateGraph ready for execution.
    """
    singleton = GraphExecuter()
    return singleton.get_graph(checkpointer)


# Global compiled graph instance (for backward compatibility)
compiled_graph = get_compiled_graph()


# if __name__ == "__main__":
#     """
#     Interactive example of the interview coach graph.

#     This demonstrates how to:
#     1. Stream the graph execution in real-time
#     2. Handle interrupts and display them to the user
#     3. Use LangGraph Command API to resume after interrupts
#     4. Loop until the workflow completes
#     """
#     from langgraph.types import Command

#     print("=" * 80)
#     print("🤖 AI INTERVIEW COACH - Interactive Demo")
#     print("=" * 80)
#     print("\nThis demo will guide you through the interview preparation process.")
#     print("Answer the questions as they appear, and type 'quit' to exit.\n")

#     # Configuration for thread persistence
#     config = {"configurable": {"thread_id": "thread-1"}}

#     # Initial user message
#     # user_input = input("👤 What job are you applying for? ")
#     # if user_input.lower() == "quit":
#     #     print("Exiting...")
#     #     exit(0)

#     user_input = """
#             [
#         {
#             "product_id": "9e5e65dc-563d-4c80-a7a4-c01e2beb02df",
#             "name": "Heavy Duty Wrench",
#             "category": "tools",
#             "price": 1200,
#             "stock_qty": 15,
#             "short_reason": "Suitable for tightening and loosening bolts and nuts in plumbing and repair tasks."
#         },
#         {
#             "product_id": "15b11d65-835d-4d2c-89c8-4ef24e350def",
#             "name": "Adjustable Hammer Drill",
#             "category": "tools",
#             "price": 8500,
#             "stock_qty": 8,
#             "short_reason": "Ideal for drilling into concrete and hard surfaces with high torque and impact mode."
#         }
#         ]
#     """

#     # Create initial state
#     initial_state = GraphState(messages=[HumanMessage(content=user_input)])

#     # Track if we're resuming from an interrupt
#     is_resuming = False
#     resume_input = None

#     # Interactive loop
#     while True:
#         print("\n" + "-" * 80)
#         print("🔄 Processing...")
#         print("-" * 80)

#         # Determine what to invoke
#         if is_resuming:
#             # Resume from checkpoint and provide the user's answer
#             # The value passed to Command(resume=...) is what interrupt() returns
#             invoke_input = Command(resume=resume_input)
#         else:
#             # First run with initial state
#             invoke_input = initial_state

#         # Stream the graph execution
#         try:
#             stream = compiled_graph.stream(
#                 invoke_input, config=config, stream_mode="values"
#             )

#             interrupt_found = False
#             last_state = None

#             for chunk in stream:
#                 # With stream_mode="values", chunk is the complete state
#                 if chunk is None:
#                     continue

#                 last_state = chunk

#                 # Check for interrupts in the state
#                 if isinstance(chunk, dict) and "__interrupt__" in chunk:
#                     interrupt_found = True
#                     interrupts = chunk["__interrupt__"]

#                     print("\n" + "=" * 80)
#                     print("⏸️  INTERRUPT DETECTED")
#                     print("=" * 80)

#                     # Display all interrupt messages
#                     for interrupt in interrupts:
#                         question = (
#                             interrupt.value
#                             if hasattr(interrupt, "value")
#                             else str(interrupt)
#                         )
#                         print(f"\n🤔 {question}\n")

#                     # Get user response
#                     user_response = input("👤 Your answer: ")

#                     if user_response.lower() == "quit":
#                         print("\n👋 Exiting interview coach. Good luck!")
#                         exit(0)

#                     # Prepare to resume with Command API
#                     is_resuming = True
#                     resume_input = user_response
#                     break

#             # If no interrupt found, check if we're done
#             if not interrupt_found:
#                 print("\n" + "=" * 80)
#                 print("✅ WORKFLOW COMPLETED!")
#                 print("=" * 80)

#                 # Display final results
#                 if last_state and isinstance(last_state, dict):
#                     print("\n📋 Final State:")

#                     user_confirmation_response = last_state.get(
#                         "user_confirmation_response"
#                     )
#                     if user_confirmation_response:
#                         print("\n✓ Requirements gathered:")
#                         if hasattr(user_confirmation_response, "model_dump"):
#                             import json

#                             print(
#                                 json.dumps(
#                                     user_confirmation_response.model_dump(),
#                                     indent=2,
#                                 )
#                             )
#                         else:
#                             print(f"{user_confirmation_response}")

#                     # interview_strategy = last_state.get("interview_strategy")
#                     # if interview_strategy:
#                     #     print("\n✓ Interview Strategy generated:")
#                     #     import json

#                     #     print(json.dumps(interview_strategy, indent=2))

#                     # interview_questions = last_state.get("interview_questions")
#                     # if interview_questions:
#                     #     print("\n✓ Interview Questions generated:")
#                     #     import json

#                     #     print(json.dumps(interview_questions, indent=2))

#                     # interview_output = last_state.get("interview_output")
#                     # if interview_output:
#                     #     print("\n✓ Interviewer generated:")
#                     #     import json

#                     #     print(json.dumps(interview_output, indent=2))

#                     # interview_evaluation = last_state.get("interview_evaluation")
#                     # if interview_evaluation:
#                     #     print("\n✓ Interview Evaluation generated:")
#                     #     import json

#                     #     print(json.dumps(interview_evaluation, indent=2))

#                 print("\n🎉 Your interview preparation is complete!")

#                 break

#         except Exception as e:
#             print(f"\n❌ Error occurred: {str(e)}")
#             import traceback

#             traceback.print_exc()
#             break

#     print("\n" + "=" * 80)
#     print("Thank you for using AI Interview Coach!")
#     print("=" * 80)
