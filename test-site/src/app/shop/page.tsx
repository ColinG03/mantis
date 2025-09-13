'use client'

export default function Shop() {
  return (
    <div className="min-h-screen">
      <div className="bg-yellow-500 p-4">
        <div className="text-black text-3xl">Our Amazing Shop</div>
      </div>

      <div className="p-8">
        <h1 className="text-4xl mb-8">Products</h1>

        {/* Product grid with accessibility issues */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Product 1 - Image without alt text */}
          <div className="border border-gray-300 p-4">
            <img src="/product1-missing.jpg" className="w-full h-48 object-cover mb-4" />
            <div className="text-xl font-bold">Amazing Widget</div>
            <div className="text-gray-600">$99.99</div>
            <div className="mt-4 bg-blue-500 text-white p-2 text-center cursor-pointer">
              Add to Cart
            </div>
          </div>

          {/* Product 2 - Button without accessible name */}
          <div className="border border-gray-300 p-4">
            <img src="/product2-broken.jpg" className="w-full h-48 object-cover mb-4" />
            <div className="text-xl font-bold">Super Gadget</div>
            <div className="text-gray-600">$149.99</div>
            <button className="mt-4 bg-red-500 text-white p-2 w-full"></button>
          </div>

          {/* Product 3 - Price not screen reader friendly */}
          <div className="border border-gray-300 p-4">
            <img src="/product3-404.jpg" className="w-full h-48 object-cover mb-4" />
            <div className="text-xl font-bold">Cool Tool</div>
            <div className="text-gray-600">
              <span className="line-through">$199.99</span>
              <span className="text-red-500 ml-2 text-2xl">$79.99</span>
            </div>
            <div className="mt-4 bg-green-500 text-white p-2 text-center cursor-pointer">
              Buy Now!
            </div>
          </div>
        </div>

        {/* Shopping cart issues */}
        <div className="mt-16 bg-gray-100 p-6">
          <h2 className="text-2xl mb-4">Shopping Cart</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <span>Amazing Widget</span>
              <span>$99.99</span>
              <div className="text-red-500 cursor-pointer">×</div>
            </div>
            <div className="flex justify-between font-bold">
              <span>Total:</span>
              <span>$99.99</span>
            </div>
            <div className="w-32 h-10 bg-orange-500 text-white flex items-center justify-center cursor-pointer">
              Checkout
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}