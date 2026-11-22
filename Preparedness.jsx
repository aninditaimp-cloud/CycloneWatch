import React, { useState } from "react";

export default function Preparedness({ items = [], cycloneName = "Cyclone Alert" }) {
  const [checkedIds, setCheckedIds] = useState({});

  const toggleItem = (id) => {
    setCheckedIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const completedCount = items.filter((item) => checkedIds[item.id]).length;

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
          alignItems: "baseline",
          gap: "8px",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "18px" }}>
          Preparedness Checklist — {cycloneName}
        </h3>
        <span style={{ fontSize: "13px", fontWeight: 600, color: "#374151" }}>
          {completedCount}/{items.length} Ready
        </span>
      </div>

      <ul style={{ listStyle: "none", padding: 0, margin: "12px 0 0 0" }}>
        {items.map((item) => {
          const isChecked = Boolean(checkedIds[item.id]);
          return (
            <li
              key={item.id}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                padding: "10px 0",
                borderBottom: "1px solid #f3f4f6",
              }}
            >
              <input
                type="checkbox"
                id={`prep-${item.id}`}
                checked={isChecked}
                onChange={() => toggleItem(item.id)}
                style={{ marginTop: "3px", cursor: "pointer" }}
              />
              <label
                htmlFor={`prep-${item.id}`}
                style={{
                  cursor: "pointer",
                  textDecoration: isChecked ? "line-through" : "none",
                  color: isChecked ? "#6b7280" : "#111827",
                }}
              >
                <strong style={{ fontSize: "13px", color: "#1d4ed8" }}>
                  [{item.category}]
                </strong>{" "}
                {item.text}
              </label>
            </li>
          );
        })}
      </ul>
    </section>
  );
}