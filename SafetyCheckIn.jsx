import React, { useEffect, useState } from "react";

export default function SafetyCheckIn({
  data,
  onConfirmSafe,
  onSendManualSos,
  onTimeoutUnresponsive,
}) {
  const shouldShow =
    Boolean(data?.trigger_checkin) || data?.zone === "Highly Dangerous";
  const initialSeconds = data?.checkin_timeout_seconds ?? 45;

  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    setSecondsLeft(initialSeconds);
    setStatusMessage("");
  }, [shouldShow, initialSeconds]);

  useEffect(() => {
    if (!shouldShow || statusMessage) return;

    if (secondsLeft <= 0) {
      setStatusMessage(
        "No response received — escalating alert to family group and rescue pipeline."
      );
      if (onTimeoutUnresponsive) {
        onTimeoutUnresponsive(data);
      }
      return;
    }

    const timer = setTimeout(() => {
      setSecondsLeft((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [shouldShow, secondsLeft, statusMessage, data, onTimeoutUnresponsive]);

  if (!shouldShow) return null;

  return (
    <section
      style={{
        border: "2px solid #dc2626",
        borderRadius: "12px",
        padding: "16px",
        backgroundColor: "#fef2f2",
      }}
    >
      <p style={{ margin: 0, fontSize: "12px", fontWeight: 700, color: "#b91c1c" }}>
        SAFETY CHECK-IN REQUIRED • ZONE: {data.zone}
      </p>
      <h3 style={{ margin: "6px 0", fontSize: "18px", color: "#7f1d1d" }}>
        Are you safe in {data.region}?
      </h3>
      <p style={{ margin: "0 0 12px 0", fontSize: "14px", color: "#374151" }}>
        {data.cyclone_name} poses a <strong>{data.severity}</strong> risk. If you do not
        respond within <strong>{secondsLeft}s</strong>, your family group will be
        notified first and then rescue SOS will escalate.
      </p>

      {statusMessage ? (
        <div
          style={{
            padding: "10px 12px",
            borderRadius: "8px",
            backgroundColor: "#fee2e2",
            color: "#991b1b",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          {statusMessage}
        </div>
      ) : (
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => {
              setStatusMessage("Marked as SAFE. Family escalation paused.");
              if (onConfirmSafe) onConfirmSafe(data);
            }}
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#15803d",
              color: "#ffffff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            I Am Safe
          </button>

          <button
            type="button"
            onClick={() => {
              setStatusMessage("Manual SOS triggered immediately.");
              if (onSendManualSos) onSendManualSos(data);
            }}
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#dc2626",
              color: "#ffffff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Send SOS Now
          </button>
        </div>
      )}
    </section>
  );
}