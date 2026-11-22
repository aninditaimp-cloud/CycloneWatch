import React, { useState } from "react";
import cycloneData from "./cyclone_data.json";
import CycloneAlert from "./CycloneAlert";
import Preparedness from "./Preparedness";
import SafetyCheckIn from "./SafetyCheckIn";

export default function App() {
  const [showCheckIn, setShowCheckIn] = useState(true);

  return (
    <div
      style={{
        maxWidth: "740px",
        margin: "24px auto",
        padding: "0 16px",
        display: "grid",
        gap: "16px",
        fontFamily: "sans-serif",
      }}
    >
      <CycloneAlert
        data={cycloneData}
        onTriggerCheckIn={() => setShowCheckIn(true)}
      />

      {showCheckIn && (
        <SafetyCheckIn
          data={cycloneData}
          onConfirmSafe={() => console.log("User confirmed safe")}
          onSendManualSos={() => console.log("Manual SOS sent")}
          onTimeoutUnresponsive={() =>
            console.log("User unresponsive -> escalate to family")
          }
        />
      )}

      <Preparedness
        items={cycloneData.precautions}
        cycloneName={cycloneData.cyclone_name}
      />
    </div>
  );
}