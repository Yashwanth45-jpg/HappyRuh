import { useState } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import ProductList from './ProductList';

function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "Hello! I'm your product assistant. How can I help you find the perfect product today?",
      timestamp: new Date(),
    },
  ]);
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (text) => {
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Clear products immediately when starting a new search
    setProducts([]);

    try {
      // Use /chat endpoint
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      console.log('Response data:', data);

      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);

      // Update products - always set products from response (even if empty array)
      if (data.is_product_query) {
        setProducts(data.products || []);
        console.log('Updated products:', data.products);
      } else {
        setProducts([]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Chat Section */}
      <div className={`${products.length > 0 ? 'flex-1' : 'w-full'} flex flex-col`}>
        {/* Header */}
        <div className="bg-gray-800 p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">Product Assistant</h1>
          <p className="text-sm text-gray-400">Ask me about our products</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 rounded-lg px-4 py-2">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>

      {/* Products Section - Show only when products exist */}
      {products.length > 0 && (
        <div className="w-96 border-l border-gray-700 bg-gray-800">
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">
              Products ({products.length})
            </h2>
          </div>
          <div className="overflow-y-auto h-[calc(100vh-80px)]">
            <ProductList products={products} />
          </div>
        </div>
      )}
    </div>
  );
}

export default Chat;