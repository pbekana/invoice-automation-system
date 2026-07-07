import React, { useState, useEffect } from 'react';
import { getVendors } from '../services/api';
import { Building, Phone, Mail, MapPin, Search, Tag, Calendar, AlertCircle } from 'lucide-react';

const Vendors = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const data = await getVendors({ search: searchTerm });
      setVendors(Array.isArray(data) ? data : data.vendors || []);
    } catch (error) {
      console.error('Failed to fetch vendors:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchVendors();
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  return (
    <div className="space-y-6">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Building className="text-blue-500" /> Vendor Directory
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Browse and manage all registered vendor profiles, default expense segments, and payment terms
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by vendor name or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-9 text-xs"
          />
        </div>
      </div>

      {/* Grid of vendors */}
      {loading && vendors.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 animate-pulse space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-200 dark:bg-slate-800 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
                </div>
              </div>
              <div className="space-y-2 pt-2">
                <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
                <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : vendors.length === 0 ? (
        <div className="card-premium p-12 text-center bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 max-w-lg mx-auto space-y-3">
          <div className="w-12 h-12 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center text-slate-400 mx-auto border border-slate-100 dark:border-slate-800">
            <Building size={20} />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800 dark:text-white">No Vendors Found</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {searchTerm 
                ? "Try searching for a different vendor name or term" 
                : "Vendors are auto-created when you upload invoices in Accounts Payable."}
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {vendors.map((vendor) => (
            <div 
              key={vendor.id || vendor._id} 
              className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex flex-col justify-between group hover:border-blue-500 dark:hover:border-blue-400 transition-all duration-200"
            >
              <div>
                {/* Logo / Badge line */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-lg border border-blue-100 dark:border-blue-900/30">
                      {(vendor.name || 'V').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-950 dark:text-white text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {vendor.name}
                      </h3>
                      <span className={`badge-saas text-[9px] px-2 py-0.5 rounded-full mt-1 ${
                        vendor.status === 'active' 
                          ? 'badge-saas-green' 
                          : 'badge-saas-red'
                      }`}>
                        {vendor.status || 'Active'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Details Section */}
                <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400 pt-2">
                  <div className="flex items-center gap-2">
                    <Mail size={13} className="text-slate-400 shrink-0" />
                    <span className="truncate">{vendor.email || 'No email registered'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone size={13} className="text-slate-400 shrink-0" />
                    <span>{vendor.phone || 'No phone registered'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={13} className="text-slate-400 shrink-0" />
                    <span className="truncate">{vendor.address || 'No address registered'}</span>
                  </div>
                </div>
              </div>

              {/* Bottom Specs */}
              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[10px]">
                <div className="flex items-center gap-1 text-slate-500">
                  <Calendar size={12} className="text-slate-400" />
                  <span>Terms: <strong className="text-slate-700 dark:text-slate-300 font-semibold">{vendor.payment_terms || 'Net 30'}</strong></span>
                </div>
                <div className="flex items-center gap-1 text-slate-500">
                  <Tag size={12} className="text-slate-400" />
                  <span>Category: <strong className="text-slate-700 dark:text-slate-300 font-semibold capitalize">{vendor.default_category || 'General'}</strong></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Vendors;
