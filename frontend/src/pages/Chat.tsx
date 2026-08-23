import { useState } from 'react';
import { sendChat } from '../api/client';
import type { ChatMessage } from '../types';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input;
    setInput('');
    const newMessages = [...messages, { role: 'user' as const, content: msg }];
    setMessages(newMessages);
    
    try {
      const res = await sendChat(newMessages);
      setMessages(prev => [...prev, { role: 'assistant' as const, content: res.response }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant' as const, content: 'Error communicating with AI.' }]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <h1 className="text-3xl font-light tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 border-b border-white/10 pb-4 mb-6">AI Copilot</h1>
      <div className="flex-1 overflow-y-auto p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl mb-6 space-y-4 shadow-2xl">
        {messages.map((m, i) => (
          <div key={i} className={`p-4 max-w-[80%] rounded-2xl text-sm leading-relaxed ${m.role === 'user' ? 'bg-indigo-500/20 border border-indigo-500/30 text-white ml-auto rounded-tr-sm shadow-[0_0_15px_rgba(99,102,241,0.15)]' : 'bg-white/5 text-gray-200 border border-white/10 rounded-tl-sm shadow-lg'}`}>
            {m.content}
          </div>
        ))}
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500 font-light">
            Ask DiskMind a question about your storage!
          </div>
        )}
      </div>
      <div className="flex gap-3">
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 p-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all duration-300 shadow-lg"
          placeholder="Ask a question..."
        />
        <button onClick={handleSend} className="px-8 py-4 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/50 font-bold hover:bg-indigo-500 hover:text-white hover:shadow-[0_0_20px_rgba(99,102,241,0.6)] transition-all duration-300">
          Send
        </button>
      </div>
    </div>
  );
}
