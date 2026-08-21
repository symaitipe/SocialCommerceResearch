import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { LANGUAGE_LABELS, LANGUAGE_COLORS } from "../config/intentConfig";

const LanguageDonut = ({ languageCounts, total }) => {
  const data = Object.entries(languageCounts || {})
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({
      name: LANGUAGE_LABELS[key] || key,
      value: count,
      color: LANGUAGE_COLORS[key] || "#94a3b8",
    }));

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
      <div
        style={{ position: "relative", width: 150, height: 150, flexShrink: 0 }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              innerRadius={48}
              outerRadius={70}
              paddingAngle={2}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ fontSize: "0.8rem", borderRadius: 8 }} />
          </PieChart>
        </ResponsiveContainer>
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          <div
            style={{ fontSize: "1.3rem", fontWeight: 800, color: "#1c1e21" }}
          >
            {total}
          </div>
          <div
            style={{ fontSize: "0.68rem", color: "#94a3b8", fontWeight: 600 }}
          >
            comments
          </div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {data.map((d, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: "0.82rem",
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: d.color,
                display: "inline-block",
              }}
            />
            <span style={{ color: "#475569", flex: 1 }}>{d.name}</span>
            <span style={{ fontWeight: 700, color: "#1c1e21" }}>{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LanguageDonut;
