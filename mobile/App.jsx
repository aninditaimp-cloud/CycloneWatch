import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
} from "react-native";

import CycloneAlert from "./src/components/CycloneAlert";
import SafetyCheckIn from "./src/components/SafetyCheckIn";
import Preparedness from "./src/components/Preparedness";
import { getActiveCyclone, getPrecautions, sendCheckIn } from "./src/services/api";

// TEMPORARY: Member 2 will replace these with real login + GPS (expo-location)
const TEST_USER_ID = "USER001";

export default function App() {
  const [cyclone, setCyclone] = useState(null);
  const [precautions, setPrecautions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [alertData, prep] = await Promise.all([
          getActiveCyclone(),
          getPrecautions(),
        ]);
        setCyclone(alertData);
        setPrecautions(prep.items);
      } catch (e) {
        setError("Cannot reach the server. Check BASE_URL in services/api.js.");
      }
    })();
  }, []);

  // Sends one of: "Safe" | "NeedHelp" | "Unresponsive"
  const report = useCallback(
    async (response) => {
      if (!cyclone) return;
      try {
        await sendCheckIn({
          userId: TEST_USER_ID,
          response,
          // TEMPORARY location = cyclone zone coordinates until GPS is added
          latitude: cyclone.coordinates.lat,
          longitude: cyclone.coordinates.lon,
          scenarioId: cyclone.scenario_id,
        });
      } catch (e) {
        // TODO (Member 2): save locally and retry with syncOfflineSos
        Alert.alert("Could not reach server", "Your response will be retried.");
      }
    },
    [cyclone]
  );

  const onConfirmSafe = useCallback(() => report("Safe"), [report]);
  const onSendManualSos = useCallback(() => report("NeedHelp"), [report]);
  const onTimeoutUnresponsive = useCallback(() => report("Unresponsive"), [report]);

  if (error) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.error}>{error}</Text>
      </SafeAreaView>
    );
  }

  if (!cyclone) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <CycloneAlert data={cyclone} />
        <SafetyCheckIn
          data={cyclone}
          onConfirmSafe={onConfirmSafe}
          onSendManualSos={onSendManualSos}
          onTimeoutUnresponsive={onTimeoutUnresponsive}
        />
        <Preparedness items={precautions} cycloneName={cyclone.cyclone_name} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#f3f4f6" },
  content: { padding: 16, gap: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  error: { color: "#991b1b", fontSize: 16, textAlign: "center" },
});
