import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
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
    if (!selectedFile || isProcessingRef.current) return;
    isProcessingRef.current = true;

    setFile(selectedFile);
    setStatus('uploading');
    setMessage('OCR scanning & AI extraction in progress...');

    try {
      const result = await uploadInvoice(selectedFile);
      setStatus('success');
      setMessage('Invoice ingested and categorized!');
      setExtractedData(result.invoice);

      if (onUploadSuccess) onUploadSuccess(result.invoice);
    } catch (err) {
      console.error(err);
      setStatus('error');
      setMessage(err.response?.data?.error || 'Failed to process document. Make sure it is a valid invoice file.');
    } finally {
      isProcessingRef.current = false;
    }
  };

  const reset = () => {
    setFile(null);
    setStatus('idle');
    setMessage('');
    setExtractedData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-md font-bold text-slate-800 dark:text-white">Upload Vendor Bill</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Upload PDF or image files. The AI engine will parse items, totals, and categorize the vendor.
        </p>
      </div>

      {status === 'idle' ? (
        <label
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
            isDragging 
              ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20' 
              : 'border-slate-300 dark:border-slate-700 hover:border-blue-500 hover:bg-slate-50 dark:hover:bg-slate-900/50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
          />

          <div className="p-3 bg-blue-50 dark:bg-slate-800 rounded-full text-blue-600 dark:text-blue-400 mb-3 border border-blue-100 dark:border-slate-800">
            <Upload size={24} />
          </div>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Click to upload or drag and drop
          </p>
          <p className="text-[10px] text-slate-400 mt-1.5">
            Supports PDF, PNG, JPG, WebP up to 16MB
          </p>
        </label>
      ) : (
        <div className="py-6 text-center border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-900/20 p-6">
          <AnimatePresence mode="wait">
            {status === 'uploading' && (
              <motion.div key="uploading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                <Loader2 className="mx-auto text-blue-500 animate-spin" size={40} />
                <div>
                  <p className="text-sm font-bold text-slate-700 dark:text-slate-300">Analyzing Document</p>
                  <p className="text-xs text-slate-400 mt-1">{message}</p>
                </div>
                {/* Visual processing timeline */}
                <div className="max-w-xs mx-auto w-full bg-slate-200 dark:bg-slate-800 h-1 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full w-2/3 animate-[pulse_1s_infinite]" />
                </div>
              </motion.div>
            )}

            {status === 'success' && (
              <motion.div key="success" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
                <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-950/30 rounded-full flex items-center justify-center mx-auto text-emerald-500 border border-emerald-100 dark:border-emerald-900/50">
                  <CheckCircle size={24} />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-white">{message}</p>
                  <p className="text-xs text-slate-400 mt-0.5">Ready for review in directory</p>
                </div>

                {extractedData && (
                  <div className="bg-white dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-left max-w-sm mx-auto shadow-sm">
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-1.5 mb-2">
                      Extracted Parameters
                    </div>
                    <div className="grid grid-cols-3 gap-y-2 gap-x-1 text-xs">
                      <span className="text-slate-400 col-span-1">Company:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 col-span-2 truncate">{extractedData.company || 'N/A'}</span>
                      <span className="text-slate-400 col-span-1">Total:</span>
                      <span className="font-bold text-blue-600 dark:text-blue-400 font-mono col-span-2">${(extractedData.total || 0).toFixed(2)}</span>
                      <span className="text-slate-400 col-span-1">Category:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 col-span-2 capitalize">{extractedData.category || 'N/A'}</span>
                    </div>
                  </div>
                )}

                <button onClick={reset} className="btn-secondary py-1.5 text-xs inline-flex items-center gap-1.5 mx-auto">
                  <RefreshCw size={12} />
                  <span>Upload Another Bill</span>
                </button>
              </motion.div>
            )}

            {status === 'error' && (
              <motion.div key="error" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
                <div className="w-12 h-12 bg-rose-50 dark:bg-rose-950/30 rounded-full flex items-center justify-center mx-auto text-rose-500 border border-rose-100 dark:border-rose-900/50">
                  <AlertCircle size={24} />
                </div>
                <div>
                  <p className="text-sm font-bold text-rose-500">{message}</p>
                  <p className="text-xs text-slate-400 mt-1">Please try uploading again or check document type.</p>
                </div>
                <button onClick={reset} className="btn-primary py-1.5 text-xs mx-auto">
                  Try Again
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default UploadInvoice;
