import React from "react";

export default function CycloneAlert({ data, onTriggerCheckIn }) {
  if (!data) return null;

  const isHighDanger =
    data.zone === "Highly Dangerous" || data.zone === "Dangerous";

  return (
    <section
      style={{
        border: "1px solid #d1d5db",
        borderRadius: "12px",
        padding: "16px",
        backgroundColor: "#ffffff",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "8px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p style={{ margin: 0, fontSize: "12px", fontWeight: 600, color: "#b91c1c" }}>
            CYCLONE EARLY WARNING • {data.alert_level}
          </p>
          <h2 style={{ margin: "4px 0", fontSize: "20px" }}>
            {data.cyclone_name} — {data.region}
          </h2>
        </div>

        <span
          style={{
            padding: "6px 12px",
            borderRadius: "999px",
            fontSize: "12px",
            fontWeight: 700,
            backgroundColor: isHighDanger ? "#fee2e2" : "#fef3c7",
            color: isHighDanger ? "#991b1b" : "#92400e",
          }}
        >
          Zone: {data.zone} ({data.severity})
        </span>
      </div>

      <p style={{ marginTop: "10px", lineHeight: 1.5 }}>{data.alert_summary}</p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "10px",
          marginTop: "12px",
          padding: "12px",
          borderRadius: "8px",
          backgroundColor: "#f9fafb",
          fontSize: "14px",
        }}
      >
        <div>
          <strong>Bhuvan Buffer:</strong> {data.impact_buffer}
        </div>
        <div>
          <strong>Wind Speed:</strong> {data.wind_speed_kmph}
        </div>
        <div>
          <strong>Lead Time:</strong> {data.lead_time_hours} hrs
        </div>
        <div>
          <strong>Coordinates:</strong> {data.coordinates?.lat}, {data.coordinates?.lon}
        </div>
      </div>

      <p style={{ marginTop: "12px", fontSize: "14px", color: "#1f2937" }}>
        <strong>Immediate Guidance:</strong> {data.recommended_action}
      </p>

      <div style={{ marginTop: "12px", fontSize: "12px", color: "#4b5563" }}>
        <strong>Sources:</strong>{" "}
        {data.sources?.map((s) => s.name).join(" • ")}
      </div>

      {onTriggerCheckIn && (
        <button
          type="button"
          onClick={onTriggerCheckIn}
          style={{
            marginTop: "14px",
            padding: "10px 14px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "#111827",
            color: "#ffffff",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Open Safety Check-In
        </button>
      )}
    </section>
  );
}