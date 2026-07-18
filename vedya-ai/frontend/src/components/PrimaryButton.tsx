"use client";
import { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "outline";
  size?: "sm" | "md" | "lg";
}

export default function PrimaryButton({
  variant = "primary",
  size = "md",
  children,
  className = "",
  type = "button",
  ...props
}: Props) {
  const classes = [
    "veda-btn",
    variant === "primary" ? "veda-btn-primary" : "veda-btn-outline",
    size === "sm" ? "veda-btn-sm" : size === "lg" ? "veda-btn-lg" : "veda-btn-md",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} type={type} {...props}>
      {children}
    </button>
  );
}
