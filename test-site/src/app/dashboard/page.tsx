'use client'

export default function Dashboard() {
  return (
    <div className="min-h-screen">
      <div className="bg-gray-800 p-4">
        <div className="text-white text-3xl">Dashboard</div>
      </div>

      <div className="p-8">
        <h1 className="text-4xl mb-8">Analytics Dashboard</h1>

        {/* Data table without proper headers */}
        <div className="mb-12">
          <h2 className="text-2xl mb-4">User Statistics</h2>
          <table className="w-full border">
            <tbody>
              <tr className="bg-gray-100">
                <td className="border p-2">Name</td>
                <td className="border p-2">Visits</td>
                <td className="border p-2">Revenue</td>
              </tr>
              <tr>
                <td className="border p-2">John Doe</td>
                <td className="border p-2">1,234</td>
                <td className="border p-2">$5,678</td>
              </tr>
              <tr>
                <td className="border p-2">Jane Smith</td>
                <td className="border p-2">2,345</td>
                <td className="border p-2">$7,890</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Charts without text alternatives */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div>
            <h3 className="text-xl mb-4">Revenue Chart</h3>
            <div className="w-full h-64 bg-gradient-to-t from-blue-500 to-blue-200 flex items-end justify-center">
              <div className="text-white">Chart Visualization</div>
            </div>
          </div>
          <div>
            <h3 className="text-xl mb-4">User Growth</h3>
            <div className="w-full h-64 bg-gradient-to-r from-green-500 to-green-200 flex items-center justify-center">
              <div className="text-white">Line Chart</div>
            </div>
          </div>
        </div>

        {/* Dynamic content without announcements */}
        <div className="mb-12">
          <h2 className="text-2xl mb-4">Live Updates</h2>
          <div className="bg-gray-100 p-4 h-32 overflow-y-auto">
            <div className="space-y-2">
              <div>New user registered: user123</div>
              <div>Sale completed: $299.99</div>
              <div>System update: Version 2.1.0</div>
            </div>
          </div>
        </div>

        {/* Focus management issues */}
        <div className="space-x-4">
          <button className="bg-blue-500 text-white px-4 py-2">Primary Action</button>
          <button className="bg-gray-500 text-white px-4 py-2" tabIndex={-1}>Unfocusable</button>
          <div className="inline-block bg-red-500 text-white px-4 py-2 cursor-pointer">Fake Button</div>
        </div>
      </div>
    </div>
  )
}