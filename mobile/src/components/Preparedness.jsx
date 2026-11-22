import React, { useState } from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

export default function Preparedness({ items = [], cycloneName = "Cyclone Alert" }) {
  const [checkedIds, setCheckedIds] = useState({});

  const toggleItem = (id) => {
    setCheckedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const completedCount = items.filter((item) => checkedIds[item.id]).length;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Preparedness Checklist — {cycloneName}</Text>
        <Text style={styles.count}>
          {completedCount}/{items.length} Ready
        </Text>
      </View>

      {items.map((item) => {
        const isChecked = Boolean(checkedIds[item.id]);
        return (
          <Pressable
            key={item.id}
            style={styles.item}
            onPress={() => toggleItem(item.id)}
          >
            {/* React Native has no built-in checkbox, so we draw one */}
            <View style={[styles.box, isChecked && styles.boxChecked]}>
              {isChecked && <Text style={styles.tick}>✓</Text>}
            </View>
            <Text
              style={[
                styles.itemText,
                isChecked && { textDecorationLine: "line-through", color: "#6b7280" },
              ]}
            >
              <Text style={styles.category}>[{item.category}] </Text>
              {item.text}
            </Text>
          </Pressable>
        );
      })}
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
  header: { marginBottom: 8 },
  title: { fontSize: 18, fontWeight: "700" },
  count: { fontSize: 13, fontWeight: "600", color: "#374151", marginTop: 2 },
  item: {
    flexDirection: "row",
    alignItems: "flex-start",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  box: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderColor: "#9ca3af",
    borderRadius: 4,
    marginRight: 10,
    marginTop: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  boxChecked: { backgroundColor: "#1d4ed8", borderColor: "#1d4ed8" },
  tick: { color: "#ffffff", fontSize: 13, fontWeight: "700" },
  itemText: { flex: 1, color: "#111827" },
  category: { fontSize: 13, fontWeight: "700", color: "#1d4ed8" },
});
