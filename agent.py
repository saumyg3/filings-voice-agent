"""Step 5: the voice agent. Callers ask about a company's 10-K and it answers from Datasphere."""
from dotenv import load_dotenv

load_dotenv()
from signalwire import AgentBase, FunctionResult  # noqa: E402

import retrieval  # noqa: E402
from companies import COMPANIES  # noqa: E402


class FilingsAgent(AgentBase):
    def __init__(self):
        super().__init__(name="filings-analyst", route="/filings")
        self.add_language("English", "en-US", "rime.spore")
        covered = ", ".join(f"{c['name']} ({c['label']})" for c in COMPANIES.values())

        self.prompt_add_section(
            "Role",
            body=f"You are a financial research assistant on a phone call. You answer questions about these SEC filings: {covered}.",
        )
        self.prompt_add_section(
            "Rules",
            bullets=[
                "Always call search_filings before answering a question about a company. Never answer from memory.",
                "Only state numbers that appear in the search results. If they don't contain the answer, say you couldn't find it in the filing.",
                "Filings report dollar amounts in millions. Say them naturally, e.g. 130,497 million is about 130.5 billion dollars.",
                "Mention which filing the answer came from.",
                "This is a phone call: one or two sentences per answer.",
                "If the caller asks about a company you don't cover, say which companies you do cover.",
            ],
        )
        self.prompt_add_section(
            "Greeting",
            body=f"Start by saying you can answer questions about {covered}, and ask what they'd like to know.",
        )

    @AgentBase.tool(
        name="search_filings",
        description="Search a company's 10-K for passages relevant to the caller's question.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look up, e.g. 'total revenue fiscal year'"},
                "company": {"type": "string", "enum": list(COMPANIES), "description": "Company tag"},
            },
            "required": ["query", "company"],
        },
    )
    def search_filings(self, args, raw_data):
        chunks = retrieval.search(args["query"], args.get("company"))
        if not chunks:
            return FunctionResult("No matching passages found in the filing.")
        return FunctionResult("\n\n---\n\n".join(c["text"] for c in chunks))


agent = FilingsAgent()

if __name__ == "__main__":
    agent.run()
