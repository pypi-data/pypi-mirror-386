from agents_boot.agents.graph import app
from agents_boot.config import cfg

def main() -> None:
    out = app.invoke({"intent": "ship v0"}, config={"configurable": {"thread_id": "cli-default"}})
    logs = out.get("logs", [])
    print("\n".join(str(x) for x in logs))
    if "spec" in out: print(out["spec"])
    if "pr" in out: print(out["pr"])

if __name__ == "__main__":
    main()
