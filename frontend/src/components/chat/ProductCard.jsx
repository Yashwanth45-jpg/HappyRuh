import React from "react";

function ProductCard({ product }) {
  const imageUrl = product.images && product.images.length > 0 
    ? product.images[0] 
    : 'https://via.placeholder.com/300x300?text=No+Image';

  return (
    <div className="bg-gray-700 rounded-lg overflow-hidden hover:bg-gray-600 transition-colors">
      <img
        src={imageUrl}
        alt={product.title || 'Product'}
        className="w-full h-48 object-cover"
        onError={(e) => {
          e.target.src = 'https://via.placeholder.com/300x300?text=Image+Error';
        }}
      />
      <div className="p-4">
        <h3 className="text-white font-semibold text-sm mb-2 line-clamp-2">
          {product.title || 'Untitled Product'}
        </h3>
        {product.description && (
          <p className="text-gray-400 text-xs mb-2 line-clamp-2">
            {product.description}
          </p>
        )}
        {product.price && (
          <p className="text-blue-400 font-bold text-lg">
            ${parseFloat(product.price).toFixed(2)}
          </p>
        )}
        {product.score && (
          <p className="text-gray-500 text-xs mt-1">
            Match: {(product.score * 100).toFixed(0)}%
          </p>
        )}
      </div>
    </div>
  );
}

export default ProductCard;
