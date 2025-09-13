'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Terrible header with no semantic HTML */}
      <div className="bg-red-500 p-4">
        <div className="text-white text-3xl font-bold">Welcome to the Worst Website Ever!</div>
        <div className="text-white">Navigate our terrible site</div>
      </div>

      {/* Navigation without proper semantics */}
      <div className="bg-gray-800 p-2">
        <div className="flex space-x-4">
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/'}>Home</div>
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/about'}>About</div>
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/contact'}>Contact</div>
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/shop'}>Shop</div>
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/blog'}>Blog</div>
          <div className="text-yellow-400 cursor-pointer hover:underline" onClick={() => window.location.href = '/dashboard'}>Dashboard</div>
        </div>
      </div>

      {/* Main content with terrible accessibility */}
      <div className="p-8">
        {/* Broken heading hierarchy */}
        <h4 className="text-2xl mb-4">Welcome!</h4>
        <h2 className="text-lg mb-2">This is our amazing homepage</h2>
        <h6 className="text-xl mb-4">Features</h6>

        {/* Image without alt text */}
        <img src="/broken-image.jpg" className="w-64 h-48 mb-4" />
        
        {/* Poor color contrast */}
        <p className="text-gray-300 bg-gray-200 p-4 mb-4">
          This text has terrible contrast and is very hard to read. Can you see this text clearly? Probably not!
        </p>

        {/* Overlapping elements */}
        <div className="relative">
          <div className="absolute top-0 left-0 bg-blue-500 text-white p-4 z-10">
            This text overlaps with other content
          </div>
          <div className="bg-red-500 text-white p-4 ml-32">
            This is behind the blue box and partially hidden
          </div>
        </div>

        {/* Form without labels */}
        <div className="mt-16 mb-8">
          <h3 className="text-xl mb-4">Newsletter Signup (Broken Form)</h3>
          <form>
            <input type="email" placeholder="Your email" className="border p-2 mr-2" />
            <input type="text" placeholder="Your name" className="border p-2 mr-2" />
            <button type="submit" className="bg-green-500 text-white p-2">Subscribe</button>
          </form>
        </div>

        {/* Links without proper context */}
        <div className="mb-8">
          <p>Check out our amazing content!</p>
          <a href="/blog" className="text-blue-500">Click here</a> | 
          <a href="/shop" className="text-blue-500 ml-2">Read more</a> | 
          <a href="/about" className="text-blue-500 ml-2">Learn more</a>
        </div>

        {/* Empty elements with dimensions */}
        <div className="w-full h-20 bg-purple-500 mb-4"></div>
        <div className="w-32 h-32 border-2 border-black mb-4"></div>

        {/* Text that's invisible */}
        <p className="text-white bg-white p-4 mb-4">
          This text is invisible because it's white text on white background
        </p>

        {/* Non-semantic button */}
        <div className="bg-orange-500 text-white p-3 cursor-pointer w-32 text-center mb-4" onClick={() => alert('Clicked!')}>
          Fake Button
        </div>

        {/* Table without proper headers */}
        <table className="border border-gray-400 mb-8">
          <tbody>
            <tr>
              <td className="border p-2">Name</td>
              <td className="border p-2">Age</td>
              <td className="border p-2">City</td>
            </tr>
            <tr>
              <td className="border p-2">John</td>
              <td className="border p-2">25</td>
              <td className="border p-2">NYC</td>
            </tr>
            <tr>
              <td className="border p-2">Jane</td>
              <td className="border p-2">30</td>
              <td className="border p-2">LA</td>
            </tr>
          </tbody>
        </table>

        {/* Elements extending outside viewport */}
        <div className="w-screen h-32 bg-pink-500 -ml-8 mb-4 overflow-hidden">
          <div className="w-full h-full bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center text-white text-2xl">
            This extends beyond the container
          </div>
        </div>

        {/* More broken content */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-red-200 p-4 h-32"></div>
          <div className="bg-green-200 p-4 h-24"></div>
          <div className="bg-blue-200 p-4 h-40"></div>
        </div>

        {/* Auto-playing video (if it existed) */}
        <video className="w-64 h-48 mb-4" autoPlay muted loop>
          <source src="/annoying-video.mp4" type="video/mp4" />
        </video>
      </div>

      {/* Footer without proper semantics */}
      <div className="bg-black text-white p-4 text-center">
        Copyright 2024 Terrible Website Inc. All rights reserved.
      </div>
    </div>
  )
}