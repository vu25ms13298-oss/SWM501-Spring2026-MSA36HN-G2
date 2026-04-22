import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function ForecastChart({ data }) {
  const chartData = data.map(f => ({
    name: f.week,
    'Dự báo': f.predicted_bookings,
    'Năng lực': f.instructor_capacity,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="Dự báo" fill="#3b82f6" />
        <Bar dataKey="Năng lực" fill="#10b981" />
      </BarChart>
    </ResponsiveContainer>
  )
}
