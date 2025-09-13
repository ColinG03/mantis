'use client'

import { useState } from 'react'

export default function Contact() {
  const [formData, setFormData] = useState({})

  return (
    <div className="min-h-screen">
      <div className="bg-green-600 p-4">
        <div className="text-white text-3xl">Contact Us</div>
      </div>

      <div className="p-8">
        <h1 className="text-4xl mb-8">Get In Touch</h1>

        {/* Terrible contact form */}
        <div className="max-w-2xl">
          <h2 className="text-2xl mb-4">Contact Form (Full of Issues)</h2>
          
          <form className="space-y-6">
            {/* Inputs without labels */}
            <div>
              <input 
                type="text" 
                placeholder="Enter your name here" 
                className="w-full border border-gray-300 p-3"
                required
              />
            </div>

            <div>
              <input 
                type="email" 
                placeholder="your.email@example.com" 
                className="w-full border border-gray-300 p-3"
                required
              />
            </div>

            <div>
              <input 
                type="tel" 
                placeholder="Phone number" 
                className="w-full border border-gray-300 p-3"
              />
            </div>

            {/* Dropdown without label */}
            <div>
              <select className="w-full border border-gray-300 p-3" required>
                <option value="">How did you hear about us?</option>
                <option value="google">Google</option>
                <option value="friend">Friend</option>
                <option value="social">Social Media</option>
              </select>
            </div>

            {/* Checkboxes without proper grouping */}
            <div>
              <div className="text-lg mb-2">What services are you interested in?</div>
              <div className="space-y-2">
                <div>
                  <input type="checkbox" id="web" value="web" />
                  <span className="ml-2">Web Development</span>
                </div>
                <div>
                  <input type="checkbox" id="mobile" value="mobile" />
                  <span className="ml-2">Mobile Apps</span>
                </div>
                <div>
                  <input type="checkbox" id="design" value="design" />
                  <span className="ml-2">Design</span>
                </div>
              </div>
            </div>

            {/* Radio buttons without proper grouping */}
            <div>
              <div className="text-lg mb-2">Project budget</div>
              <div className="space-y-2">
                <div>
                  <input type="radio" name="budget" value="small" />
                  <span className="ml-2">Under $5,000</span>
                </div>
                <div>
                  <input type="radio" name="budget" value="medium" />
                  <span className="ml-2">$5,000 - $15,000</span>
                </div>
                <div>
                  <input type="radio" name="budget" value="large" />
                  <span className="ml-2">Over $15,000</span>
                </div>
              </div>
            </div>

            {/* Textarea without label */}
            <div>
              <textarea 
                placeholder="Tell us about your project..." 
                rows={5}
                className="w-full border border-gray-300 p-3"
                required
              ></textarea>
            </div>

            {/* File upload without proper instructions */}
            <div>
              <input type="file" className="w-full border border-gray-300 p-3" />
            </div>

            {/* Fake CAPTCHA without alternative */}
            <div>
              <div className="bg-gray-200 p-4 mb-2">
                <div className="text-sm mb-2">CAPTCHA: What is 5 + 3?</div>
                <input type="text" className="border border-gray-300 p-2 w-20" />
              </div>
            </div>

            {/* Agreement checkbox without proper association */}
            <div className="flex items-start space-x-2">
              <input type="checkbox" required className="mt-1" />
              <div className="text-sm">
                I agree to the terms and conditions and privacy policy and marketing emails and cookies and everything else.
              </div>
            </div>

            {/* Multiple submit buttons that are confusing */}
            <div className="space-x-4">
              <button type="submit" className="bg-blue-500 text-white px-6 py-3">
                Submit
              </button>
              <button type="button" className="bg-green-500 text-white px-6 py-3">
                Send
              </button>
              <div className="inline-block bg-red-500 text-white px-6 py-3 cursor-pointer">
                Submit Form
              </div>
            </div>
          </form>
        </div>

        {/* Contact information with poor markup */}
        <div className="mt-16">
          <h2 className="text-2xl mb-4">Other Ways to Reach Us</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="text-xl font-bold mb-2">Phone</div>
              <div>Call us at 123-456-7890</div>
              <div>Available Monday through Friday</div>
            </div>
            
            <div>
              <div className="text-xl font-bold mb-2">Email</div>
              <div>Send us an email at contact@terrible-site.com</div>
              <div>We'll respond within 24 hours</div>
            </div>
            
            <div>
              <div className="text-xl font-bold mb-2">Address</div>
              <div>123 Fake Street</div>
              <div>Nowhere City, NC 12345</div>
              <div>United States</div>
            </div>
          </div>
        </div>

        {/* Embedded map without alternative */}
        <div className="mt-16">
          <h2 className="text-2xl mb-4">Find Us</h2>
          <div className="w-full h-64 bg-gray-400 flex items-center justify-center">
            <div className="text-gray-600">Interactive Map Would Go Here</div>
          </div>
        </div>

        {/* Social media links without proper labels */}
        <div className="mt-16">
          <h2 className="text-2xl mb-4">Follow Us</h2>
          <div className="flex space-x-4">
            <a href="#" className="w-10 h-10 bg-blue-600 rounded"></a>
            <a href="#" className="w-10 h-10 bg-blue-400 rounded"></a>
            <a href="#" className="w-10 h-10 bg-pink-500 rounded"></a>
            <a href="#" className="w-10 h-10 bg-red-600 rounded"></a>
          </div>
        </div>

        {/* FAQ section with poor structure */}
        <div className="mt-16">
          <h2 className="text-2xl mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div className="border border-gray-300 p-4">
              <div className="font-bold">How long does a project take?</div>
              <div>It depends on the scope but usually 2-6 months.</div>
            </div>
            <div className="border border-gray-300 p-4">
              <div className="font-bold">What is your hourly rate?</div>
              <div>Our rates vary by project complexity.</div>
            </div>
            <div className="border border-gray-300 p-4">
              <div className="font-bold">Do you work with small businesses?</div>
              <div>Yes, we work with businesses of all sizes.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}