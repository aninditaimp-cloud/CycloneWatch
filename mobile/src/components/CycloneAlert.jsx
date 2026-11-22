import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

export default function CycloneAlert({ data, onTriggerCheckIn }) {
  if (!data) return null;

  const isHighDanger =
    data.zone === "Highly Dangerous" || data.zone === "Dangerous";

  return (
    <View style={styles.card}>
      <Text style={styles.alertLabel}>CYCLONE EARLY WARNING • {data.alert_level}</Text>
      <Text style={styles.title}>
        {data.cyclone_name} — {data.region}
      </Text>

      <View
        style={[
          styles.badge,
          { backgroundColor: isHighDanger ? "#fee2e2" : "#fef3c7" },
        ]}
      >
        <Text
          style={[
            styles.badgeText,
            { color: isHighDanger ? "#991b1b" : "#92400e" },
          ]}
        >
          Zone: {data.zone} ({data.severity})
        </Text>
      </View>

      <Text style={styles.summary}>{data.alert_summary}</Text>

      <View style={styles.infoBox}>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Bhuvan Buffer: </Text>
          {data.impact_buffer}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Wind Speed: </Text>
          {data.wind_speed_kmph}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Lead Time: </Text>
          {data.lead_time_hours} hrs
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Coordinates: </Text>
          {data.coordinates?.lat}, {data.coordinates?.lon}
        </Text>
      </View>

      <Text style={styles.guidance}>
        <Text style={styles.bold}>Immediate Guidance: </Text>
        {data.recommended_action}
      </Text>

      <Text style={styles.sources}>
        <Text style={styles.bold}>Sources: </Text>
        {data.sources?.map((s) => s.name).join(" • ")}
      </Text>

      {onTriggerCheckIn && (
        <Pressable style={styles.button} onPress={onTriggerCheckIn}>
          <Text style={styles.buttonText}>Open Safety Check-In</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 12,
    padding: 16,
    backgroundColor: "#ffffff",
  },
  alertLabel: { fontSize: 12, fontWeight: "600", color: "#b91c1c" },
  title: { fontSize: 20, fontWeight: "700", marginVertical: 6 },
  badge: {
    alignSelf: "flex-start",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
  },
  badgeText: { fontSize: 12, fontWeight: "700" },
  summary: { marginTop: 10, lineHeight: 21 },
  infoBox: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
    backgroundColor: "#f9fafb",
    gap: 4,
  },
  infoText: { fontSize: 14 },
  bold: { fontWeight: "700" },
  guidance: { marginTop: 12, fontSize: 14, color: "#1f2937" },
  sources: { marginTop: 12, fontSize: 12, color: "#4b5563" },
  button: {
    marginTop: 14,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: "#111827",
    alignSelf: "flex-start",
  },
  buttonText: { color: "#ffffff", fontWeight: "600" },
});
