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
} from "recharts";

function DashboardCharts({ dailyUsage, dashboardSummary }) {
  const usageData = [
    {
      name: "Requests",
      value: dailyUsage?.requests_today || 0,
    },
    {
      name: "Characters",
      value: dailyUsage?.characters_used || 0,
    },
  ];

  const summaryData = [
    {
      name: "Sessions",
      value: dashboardSummary?.total_sessions || 0,
    },
    {
      name: "Documents",
      value: dashboardSummary?.total_documents || 0,
    },
    {
      name: "AI Requests",
      value: dashboardSummary?.total_ai_requests || 0,
    },
  ];

  const COLORS = [
    "#6366f1",
    "#06b6d4",
    "#8b5cf6",
  ];

  return (
    <div className="dashboard-chart-grid">
      <div className="dashboard-chart-card">
        <h3>Daily Usage</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={usageData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />

            <Bar
              dataKey="value"
              fill="#6366f1"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="dashboard-chart-card">
        <h3>Workspace Summary</h3>

        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={summaryData}
              dataKey="value"
              outerRadius={110}
              label
            >
              {summaryData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default DashboardCharts;