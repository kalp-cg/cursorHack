"use client";

interface Props {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
  retryLabel?: string;
  dismissLabel?: string;
}

/** Inline, visible error — never silent console-only failures. */
export default function ErrorBanner({
  message,
  onDismiss,
  onRetry,
  retryLabel = "Retry",
  dismissLabel = "Dismiss",
}: Props) {
  if (!message) return null;
  return (
    <div className="veda-error-banner" role="alert">
      <p>{message}</p>
      <div className="veda-error-banner-actions">
        {onRetry && (
          <button type="button" onClick={onRetry}>
            {retryLabel}
          </button>
        )}
        {onDismiss && (
          <button type="button" className="is-ghost" onClick={onDismiss}>
            {dismissLabel}
          </button>
        )}
      </div>
    </div>
  );
}
