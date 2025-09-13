'use client'

export default function About() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-purple-600 p-4">
        <div className="text-white text-3xl">About Us</div>
      </div>

      <div className="p-8">
        {/* Broken images */}
        <h1 className="text-4xl mb-4">Learn About Our Company</h1>
        
        <div className="grid grid-cols-2 gap-8 mb-8">
          <div>
            <img src="/team-photo-404.jpg" className="w-full h-64 object-cover mb-4" />
            <p>Our amazing team photo that doesn't exist</p>
          </div>
          <div>
            <img src="/office-broken.png" className="w-full h-64 object-cover mb-4" />
            <p>Our beautiful office space</p>
          </div>
        </div>

        {/* Invisible text due to CSS */}
        <h2 className="text-2xl mb-4">Our Mission</h2>
        <p className="text-transparent mb-4">
          This text is completely invisible due to CSS, but it contains important information about our mission and values.
        </p>

        {/* Text with zero opacity */}
        <p className="opacity-0 mb-4">
          This paragraph has zero opacity so it's invisible to users but still in the DOM.
        </p>

        {/* Elements positioned outside viewport */}
        <div className="relative overflow-hidden h-64 mb-8">
          <div className="absolute -left-full top-0 bg-red-500 text-white p-4 w-64">
            This content is positioned outside the viewport to the left
          </div>
          <div className="absolute -right-full top-0 bg-blue-500 text-white p-4 w-64">
            This content is positioned outside the viewport to the right
          </div>
          <div className="absolute top-0 left-0 bg-green-500 text-white p-4">
            Visible content
          </div>
        </div>

        {/* Empty clickable elements */}
        <div className="mb-8">
          <h3 className="text-xl mb-4">Our Services</h3>
          <div className="flex space-x-4">
            <button className="w-32 h-16 bg-blue-500"></button>
            <div className="w-32 h-16 bg-red-500 cursor-pointer" onClick={() => {}}></div>
            <a href="/services" className="block w-32 h-16 bg-green-500"></a>
          </div>
        </div>

        {/* Keyboard navigation issues */}
        <div className="mb-8">
          <h3 className="text-xl mb-4">Interactive Elements (Broken Navigation)</h3>
          <div className="space-y-4">
            <div tabIndex={-1} className="bg-gray-300 p-3 cursor-pointer" onClick={() => alert('Clicked!')}>
              This element can't be reached with keyboard
            </div>
            <div tabIndex={0} className="bg-gray-300 p-3 cursor-pointer">
              This element can be focused but has no action
            </div>
            <div className="bg-gray-300 p-3 cursor-pointer" onClick={() => window.open('/popup', '_blank')}>
              This opens a popup without warning
            </div>
          </div>
        </div>

        {/* Hidden content that should be visible */}
        <div className="mb-8">
          <h3 className="text-xl mb-4">Company History</h3>
          <details className="mb-4">
            <summary className="cursor-pointer text-blue-600">Click to expand our history</summary>
            <div className="hidden">
              <p>This content is hidden even when the details element is expanded due to CSS hiding it.</p>
            </div>
          </details>
        </div>

        {/* Overlapping interactive elements */}
        <div className="relative mb-8">
          <h3 className="text-xl mb-4">Contact Our Team</h3>
          <button className="absolute top-8 left-0 bg-blue-500 text-white p-3 z-10">
            Primary Button
          </button>
          <button className="absolute top-8 left-20 bg-red-500 text-white p-3">
            Overlapped Button
          </button>
          <div className="h-20"></div>
        </div>

        {/* Content with poor structure */}
        <div className="mb-8">
          <div className="text-2xl font-bold mb-2">This looks like a heading but isn't</div>
          <span className="block text-lg mb-2">This is a span used as a paragraph</span>
          <div className="text-sm">
            <div>Nested divs</div>
            <div>Instead of</div>
            <div>Proper list items</div>
          </div>
        </div>

        {/* Element that causes horizontal scroll */}
        <div className="w-screen bg-yellow-300 h-16 -ml-8 mb-4 flex items-center justify-center">
          This element extends beyond the container causing horizontal scroll
        </div>

        {/* Inaccessible media controls */}
        <div className="mb-8">
          <h3 className="text-xl mb-4">Company Video</h3>
          <div className="relative bg-black w-64 h-48">
            <div className="absolute inset-0 flex items-center justify-center text-white">
              Video Player Placeholder
            </div>
            <div className="absolute bottom-2 left-2 right-2 flex justify-between">
              <div className="w-6 h-6 bg-white cursor-pointer" title="Play"></div>
              <div className="w-6 h-6 bg-white cursor-pointer" title="Volume"></div>
              <div className="w-6 h-6 bg-white cursor-pointer" title="Settings"></div>
            </div>
          </div>
        </div>

        {/* Form with accessibility issues */}
        <div className="mb-8">
          <h3 className="text-xl mb-4">Quick Contact Form</h3>
          <form className="space-y-4">
            <input type="text" placeholder="Name" className="block w-full border p-2" />
            <input type="email" placeholder="Email" className="block w-full border p-2" />
            <textarea placeholder="Message" className="block w-full border p-2 h-24"></textarea>
            <div className="w-32 h-10 bg-green-500 text-white flex items-center justify-center cursor-pointer">
              Send
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}