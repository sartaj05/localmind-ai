import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";

function DashboardCharts({
  dailyRequests = [],
  modelUsage = [],
  successRate = [],
}) {
  const normalizedDaily = dailyRequests.map((item) => ({
    date: item.date?.slice(5) || item.date,
    requests: item.requests || 0,
  }));

  const normalizedModels = modelUsage.length
    ? modelUsage
    : [{ model: "No data", count: 1 }];

  const normalizedSuccess = successRate.length
    ? successRate
    : [{ name: "No data", value: 1 }];

  const COLORS = ["#4f46e5", "#06b6d4", "#22c55e", "#f97316", "#ef4444"];

  return (
    <div className="dashboard-chart-grid">
      <div className="dashboard-chart-card">
        <h3>7-Day Requests</h3>

        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={normalizedDaily}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />

            <Line
              type="monotone"
              dataKey="requests"
              name="Requests"
              stroke="#4f46e5"
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="dashboard-chart-card">
        <h3>Model Usage</h3>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={normalizedModels}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="model" />
            <YAxis allowDecimals={false} />
            <Tooltip />

            <Bar dataKey="count" name="Requests" fill="#06b6d4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="dashboard-chart-card">
        <h3>Success vs Failed</h3>

        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={normalizedSuccess}
              dataKey="value"
              nameKey="name"
              outerRadius={95}
              label
            >
              {normalizedSuccess.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default DashboardCharts;