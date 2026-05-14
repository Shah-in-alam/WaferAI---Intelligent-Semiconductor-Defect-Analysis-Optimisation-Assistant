import { CircuitBoard, Layers, MessageSquare, BarChart3, FileText, Github } from "lucide-react";

type NavKey = "analyze" | "history" | "chat" | "reports";

interface Props {
  active: NavKey;
  onChange: (k: NavKey) => void;
}

export function Sidebar({ active, onChange }: Props) {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-ink-200 bg-white px-4 py-6 dark:border-ink-800 dark:bg-ink-900 lg:flex">
      <div className="flex items-center gap-2.5 px-2">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
          <CircuitBoard size={20} />
        </div>
        <div>
          <p className="text-base font-semibold tracking-tight text-ink-900 dark:text-ink-50">
            WaferAI
          </p>
          <p className="label-mono mt-0.5">Defect intelligence</p>
        </div>
      </div>

      <nav className="mt-8 flex flex-col gap-1">
        <p className="label-mono px-2 pb-2">Workspace</p>
        <NavButton
          icon={<Layers size={16} />}
          label="Analyse wafer"
          active={active === "analyze"}
          onClick={() => onChange("analyze")}
        />
        <NavButton
          icon={<MessageSquare size={16} />}
          label="Chat"
          active={active === "chat"}
          onClick={() => onChange("chat")}
          dim
        />
        <NavButton
          icon={<BarChart3 size={16} />}
          label="History"
          active={active === "history"}
          onClick={() => onChange("history")}
          dim
        />
        <NavButton
          icon={<FileText size={16} />}
          label="Reports"
          active={active === "reports"}
          onClick={() => onChange("reports")}
          dim
        />
      </nav>

      <div className="mt-auto space-y-2 px-2">
        <p className="label-mono">Resources</p>
        <a
          href="https://github.com/Shah-in-alam"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-ink-500 transition hover:text-brand-600 dark:hover:text-brand-300"
        >
          <Github size={14} /> Source
        </a>
        <p className="text-[10px] text-ink-400">
          Built on WM-811K · 811K wafers
        </p>
      </div>
    </aside>
  );
}

function NavButton({
  icon,
  label,
  active,
  onClick,
  dim,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  dim?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={active ? "nav-item-active" : "nav-item-inactive"}
    >
      <span className="grid h-6 w-6 place-items-center">{icon}</span>
      <span className="flex-1 text-left">{label}</span>
      {dim && !active ? (
        <span className="text-[10px] uppercase tracking-wide text-ink-400">
          Soon
        </span>
      ) : null}
    </button>
  );
}

export type { NavKey };
