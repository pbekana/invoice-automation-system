// import React, { useState, useRef } from 'react';
// import { Upload, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
// import { uploadInvoice } from '../services/api';
// import { motion, AnimatePresence } from 'framer-motion';

// const UploadInvoice = ({ onUploadSuccess }) => {
//   const [isDragging, setIsDragging] = useState(false);
//   const [file, setFile] = useState(null);
//   const [status, setStatus] = useState('idle'); // idle, uploading, success, error
//   const [message, setMessage] = useState('');
//   const [extractedData, setExtractedData] = useState(null);
//   const fileInputRef = useRef(null);

//   const handleDragOver = (e) => {
//     e.preventDefault();
//     setIsDragging(true);
//   };

//   const handleDragLeave = () => {
//     setIsDragging(false);
//   };

//   const handleDrop = (e) => {
//     e.preventDefault();
//     setIsDragging(false);
//     const droppedFile = e.dataTransfer.files[0];
//     if (droppedFile) processFile(droppedFile);
//   };

//   const handleFileChange = (e) => {
//     const selectedFile = e.target.files[0];
//     if (selectedFile) processFile(selectedFile);
//   };

//   const processFile = async (selectedFile) => {
//     setFile(selectedFile);
//     setStatus('uploading');
//     setMessage('Processing your invoice with AI...');

//     try {
//       const result = await uploadInvoice(selectedFile);
//       setStatus('success');
//       setMessage('Invoice processed successfully!');
//       setExtractedData(result.invoice);
      
//       if (onUploadSuccess) {
//         onUploadSuccess(result.invoice);
//       }
//     } catch (err) {
//       console.error(err);
//       setStatus('error');
//       setMessage(err.response?.data?.error || 'Failed to upload invoice. Please try again.');
//     }
//   };

//   const reset = () => {
//     setFile(null);
//     setStatus('idle');
//     setMessage('');
//     setExtractedData(null);
//     if (fileInputRef.current) fileInputRef.current.value = '';
//   };

//   return (
//     <motion.div 
//       initial={{ opacity: 0, y: 20 }}
//       animate={{ opacity: 1, y: 0 }}
//       className="glass-card fade-in"
//     >
//       <h2 className="text-xl font-bold mb-4">Upload Invoice</h2>
//       <p className="text-sm text-gray-400 mb-6">
//         Upload your PDF or image invoices. Our AI will automatically extract data and categorize your expenses.
//       </p>

//       {status === 'idle' ? (
//         <div
//           className={`upload-zone ${isDragging ? 'dragging' : ''}`}
//           onDragOver={handleDragOver}
//           onDragLeave={handleDragLeave}
//           onDrop={handleDrop}
//           onClick={() => fileInputRef.current?.click()}
//         >
//           <input
//             type="file"
//             ref={fileInputRef}
//             onChange={handleFileChange}
//             className="hidden"
//             accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
//           />
//           <Upload className="mx-auto mb-4 text-indigo-400" size={48} />
//           <p className="font-semibold">Click to upload or drag and drop</p>
//           <p className="text-xs text-gray-400 mt-2">Support: PDF, PNG, JPG, WebP (Max 16MB)</p>
//         </div>
//       ) : (
//         <div className="py-8 text-center">
//           <AnimatePresence mode="wait">
//             {status === 'uploading' && (
//               <motion.div 
//                 key="uploading"
//                 initial={{ opacity: 0 }}
//                 animate={{ opacity: 1 }}
//                 exit={{ opacity: 0 }}
//               >
//                 <Loader2 className="mx-auto mb-4 text-indigo-400 animate-spin" size={48} />
//                 <p className="font-semibold text-indigo-400">{message}</p>
//               </motion.div>
//             )}

//             {status === 'success' && (
//               <motion.div 
//                 key="success"
//                 initial={{ opacity: 0, scale: 0.9 }}
//                 animate={{ opacity: 1, scale: 1 }}
//                 className="space-y-4"
//               >
//                 <CheckCircle className="mx-auto text-emerald-400" size={48} />
//                 <p className="font-semibold text-emerald-400">{message}</p>
                
//                 {extractedData && (
//                   <div className="bg-slate-800/50 p-4 rounded-lg text-left max-w-sm mx-auto border border-emerald-500/20">
//                     <div className="grid grid-cols-2 gap-2 text-sm">
//                       <span className="text-gray-400">Company:</span>
//                       <span className="font-medium">{extractedData.company}</span>
//                       <span className="text-gray-400">Total:</span>
//                       <span className="font-medium text-emerald-300 font-mono">${extractedData.total.toFixed(2)}</span>
//                       <span className="text-gray-400">Category:</span>
//                       <span className="font-medium italic">{extractedData.category}</span>
//                     </div>
//                   </div>
//                 )}
                
//                 <button onClick={reset} className="btn btn-primary btn-sm">
//                   Upload Another
//                 </button>
//               </motion.div>
//             )}

//             {status === 'error' && (
//               <motion.div 
//                 key="error"
//                 initial={{ opacity: 0, scale: 0.9 }}
//                 animate={{ opacity: 1, scale: 1 }}
//               >
//                 <AlertCircle className="mx-auto mb-4 text-rose-400" size={48} />
//                 <p className="font-semibold text-rose-400">{message}</p>
//                 <button onClick={reset} className="btn btn-primary btn-sm mt-4">
//                   Try Again
//                 </button>
//               </motion.div>
//             )}
//           </AnimatePresence>
//         </div>
//       )}
//     </motion.div>
//   );
// };

// export default UploadInvoice;
import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadInvoice } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const UploadInvoice = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error
  const [message, setMessage] = useState('');
  const [extractedData, setExtractedData] = useState(null);
  const fileInputRef = useRef(null);

  // Prevent double processing
  const isProcessingRef = useRef(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) processFile(droppedFile);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) processFile(selectedFile);
  };

  const processFile = async (selectedFile) => {
    if (!selectedFile || isProcessingRef.current) return; // ✅ prevent double upload
    isProcessingRef.current = true;

    setFile(selectedFile);
    setStatus('uploading');
    setMessage('Processing your invoice with AI...');

    try {
      const result = await uploadInvoice(selectedFile);
      setStatus('success');
      setMessage('Invoice processed successfully!');
      setExtractedData(result.invoice);

      if (onUploadSuccess) onUploadSuccess(result.invoice);
    } catch (err) {
      console.error(err);
      setStatus('error');
      setMessage(err.response?.data?.error || 'Failed to upload invoice. Please try again.');
    } finally {
      isProcessingRef.current = false; // allow new uploads
    }
  };

  const reset = () => {
    setFile(null);
    setStatus('idle');
    setMessage('');
    setExtractedData(null);
    if (fileInputRef.current) fileInputRef.current.value = ''; // ✅ reset input
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card fade-in">
      <h2 className="text-xl font-bold mb-4">Upload Invoice</h2>
      <p className="text-sm text-gray-400 mb-6">
        Upload your PDF or image invoices. Our AI will automatically extract data and categorize your expenses.
      </p>

      {status === 'idle' ? (
       <label
  className={`border-2 border-dashed border-gray-600 rounded-xl p-8 text-center w-full ${isDragging ? 'border-indigo-400' : ''}`}
  onDragOver={handleDragOver}
  onDragLeave={handleDragLeave}
  onDrop={handleDrop}
  style={{ cursor: 'pointer' }}
>
  <input
    type="file"
    ref={fileInputRef}
    onChange={handleFileChange}
    className="hidden"
    accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
  />

  <Upload className="mx-auto mb-4 text-indigo-400" size={48} />
  <p className="font-semibold">Click to upload or drag and drop</p>
  <p className="text-xs text-gray-400 mt-2">
    Support: PDF, PNG, JPG, WebP (Max 16MB)
  </p>
</label>
      ) : (
        <div className="py-8 text-center">
          <AnimatePresence mode="wait">
            {status === 'uploading' && (
              <motion.div key="uploading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Loader2 className="mx-auto mb-4 text-indigo-400 animate-spin" size={48} />
                <p className="font-semibold text-indigo-400">{message}</p>
              </motion.div>
            )}

            {status === 'success' && (
              <motion.div key="success" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
                <CheckCircle className="mx-auto text-emerald-400" size={48} />
                <p className="font-semibold text-emerald-400">{message}</p>

                {extractedData && (
                  <div className="bg-slate-800/50 p-4 rounded-lg text-left max-w-sm mx-auto border border-emerald-500/20">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <span className="text-gray-400">Company:</span>
                      <span className="font-medium">{extractedData.company}</span>
                      <span className="text-gray-400">Total:</span>
                      <span className="font-medium text-emerald-300 font-mono">${extractedData.total.toFixed(2)}</span>
                      <span className="text-gray-400">Category:</span>
                      <span className="font-medium italic">{extractedData.category}</span>
                    </div>
                  </div>
                )}

                <button onClick={reset} className="btn btn-primary btn-sm">
                  Upload Another
                </button>
              </motion.div>
            )}

            {status === 'error' && (
              <motion.div key="error" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
                <AlertCircle className="mx-auto mb-4 text-rose-400" size={48} />
                <p className="font-semibold text-rose-400">{message}</p>
                <button onClick={reset} className="btn btn-primary btn-sm mt-4">
                  Try Again
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
};

export default UploadInvoice;

