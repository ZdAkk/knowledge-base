import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "border-border text-foreground",
        muted: "border-transparent bg-muted text-muted-foreground",
        amber: "border-amber-500/30 bg-amber-500/10 text-amber-400",
        rose: "border-rose-500/30 bg-rose-500/10 text-rose-400",
        emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
        blue: "border-blue-500/30 bg-blue-500/10 text-blue-400",
        violet: "border-violet-500/30 bg-violet-500/10 text-violet-400",
        slate: "border-slate-500/30 bg-slate-500/10 text-slate-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
