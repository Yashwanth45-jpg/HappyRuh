import React, { useState } from "react";

function ProductCard({ product }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Get first image or use placeholder
  const imageUrl = product.images && product.images.length > 0 
    ? product.images[0] 
    : 'https://via.placeholder.com/300x200?text=No+Image';

  // Format price in Rupees
  const formattedPrice = product.price 
    ? `₹${parseFloat(product.price).toFixed(2)}` 
    : 'Price not available';

  // Parse description into bullet points
  const formatDescription = (desc) => {
    if (!desc) return ['No description available for this product.'];
    
    // Split by common separators: periods, semicolons, or newlines
    // Filter out empty strings and trim whitespace
    const points = desc
      .split(/[.;]\s+|\n/)
      .map(point => point.trim())
      .filter(point => point.length > 10); // Only include meaningful points
    
    return points.length > 0 ? points : [desc];
  };

  const descriptionPoints = formatDescription(product.description);

  return (
    <>
      {/* Backdrop overlay when expanded */}
      {isExpanded && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsExpanded(false)}
        />
      )}

      {/* Product Card */}
      <div 
        className="bg-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-all duration-200 cursor-pointer relative"
        onClick={() => setIsExpanded(true)}
      >
        {/* Product Image */}
        <div className="relative h-48 bg-gray-800">
          <img
            src={imageUrl}
            alt={product.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/300x200?text=Image+Not+Found';
            }}
          />
        </div>

        {/* Product Info */}
        <div className="p-4">
          <h3 className="text-white font-semibold text-sm mb-2 line-clamp-2">
            {product.title}
          </h3>
          <p className="text-blue-400 text-lg font-bold">{formattedPrice}</p>
        </div>
      </div>

      {/* Side Panel - Slide in from right */}
      <div 
        className={`fixed top-0 right-0 h-full w-[500px] bg-gray-800 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          isExpanded ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Close button */}
        <button
          onClick={() => setIsExpanded(false)}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Panel Content */}
        <div className="h-full overflow-y-auto p-6">
          {/* Product Image */}
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <img
              src={imageUrl}
              alt={product.title}
              className="w-full h-80 object-contain"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/400x400?text=Image+Not+Found';
              }}
            />
          </div>

          {/* Product Title */}
          <h2 className="text-2xl font-bold text-white mb-4">
            {product.title}
          </h2>

          {/* Price */}
          <p className="text-3xl font-bold text-blue-400 mb-6">
            {formattedPrice}
          </p>

          {/* Description - Bullet Points */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
              Description
            </h3>
            <ul className="space-y-3">
              {descriptionPoints.map((point, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-400 mr-3 mt-1 flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </span>
                  <span className="text-gray-300 text-base leading-relaxed">
                    {point}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Product Details */}
          {product.product_type && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                Product Type
              </h3>
              <p className="text-gray-300 text-base">
                {product.product_type}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default ProductCard;
