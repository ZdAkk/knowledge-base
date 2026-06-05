import { NavLink } from "react-router-dom";
import { Moon, BookOpen, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/dreams", label: "Dreams", icon: Moon },
  { to: "/books", label: "Books", icon: BookOpen },
];

export function Sidebar() {
  return (
    <aside className="flex flex-col w-56 min-h-screen border-r border-border bg-card/50 px-3 py-6 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-2 mb-8">
        <div className="w-7 h-7 rounded-md bg-primary/20 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
        <span className="font-medium text-sm tracking-wide text-foreground">
          Knowledge Base
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-2 pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground/60">Self-hosted RAG</p>
      </div>
    </aside>
  );
}
