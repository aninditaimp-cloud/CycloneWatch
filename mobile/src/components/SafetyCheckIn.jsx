import React, { useEffect, useState } from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

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
    <View style={styles.card}>
      <Text style={styles.label}>
        SAFETY CHECK-IN REQUIRED • ZONE: {data.zone}
      </Text>
      <Text style={styles.title}>Are you safe in {data.region}?</Text>
      <Text style={styles.body}>
        {data.cyclone_name} poses a{" "}
        <Text style={styles.bold}>{data.severity}</Text> risk. If you do not
        respond within <Text style={styles.bold}>{secondsLeft}s</Text>, your
        family group will be notified first and then rescue SOS will escalate.
      </Text>

      {statusMessage ? (
        <View style={styles.statusBox}>
          <Text style={styles.statusText}>{statusMessage}</Text>
        </View>
      ) : (
        <View style={styles.row}>
          <Pressable
            style={[styles.button, { backgroundColor: "#15803d" }]}
            onPress={() => {
              setStatusMessage("Marked as SAFE. Family escalation paused.");
              if (onConfirmSafe) onConfirmSafe(data);
            }}
          >
            <Text style={styles.buttonText}>I Am Safe</Text>
          </Pressable>

          <Pressable
            style={[styles.button, { backgroundColor: "#dc2626" }]}
            onPress={() => {
              setStatusMessage("Manual SOS triggered immediately.");
              if (onSendManualSos) onSendManualSos(data);
            }}
          >
            <Text style={styles.buttonText}>Send SOS Now</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 2,
    borderColor: "#dc2626",
    borderRadius: 12,
    padding: 16,
    backgroundColor: "#fef2f2",
  },
  label: { fontSize: 12, fontWeight: "700", color: "#b91c1c" },
  title: { fontSize: 18, fontWeight: "700", color: "#7f1d1d", marginVertical: 6 },
  body: { fontSize: 14, color: "#374151", marginBottom: 12 },
  bold: { fontWeight: "700" },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  button: { paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8 },
  buttonText: { color: "#ffffff", fontWeight: "700" },
  statusBox: { padding: 10, borderRadius: 8, backgroundColor: "#fee2e2" },
  statusText: { color: "#991b1b", fontWeight: "600", fontSize: 14 },
});
