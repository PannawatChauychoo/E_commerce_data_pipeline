"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, Eye, ChevronDown, ChevronRight, File, Calendar, Loader2, FolderDown } from 'lucide-react';
import Papa from 'papaparse';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Separator } from './ui/separator';

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";

interface FileInfo {
  name: string;
  size: string;
  path: string;
}

interface SimulationRun {
  id: string;
  date: string;
  time: string;
  files: FileInfo[];
}

interface FileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function FileSidebar({ isOpen, onClose }: FileSidebarProps) {
  const [expandedRuns, setExpandedRuns] = useState<Set<string>>(new Set());
  const [expandedPreviews, setExpandedPreviews] = useState<Set<string>>(new Set());
  const [previewData, setPreviewData] = useState<Record<string, any[]>>({});
  const [simulationRuns, setSimulationRuns] = useState<SimulationRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clickedRuns, setClickedRuns] = useState<Set<string>>(new Set());

  // Fetch simulation runs from API
  useEffect(() => {
    if (isOpen) {
      fetchSimulationRuns();
    }
  }, [isOpen]);

  const fetchSimulationRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_ORIGIN}/api/files/list/`);
      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }
      const data = await response.json();

      // Transform API data to match our interface
      const transformedRuns: SimulationRun[] = data.runs.map((run: any) => ({
        id: run.id,
        date: run.date,
        time: new Date(run.time * 1000).toLocaleString(), // Convert timestamp to readable date/time
        files: run.files.map((file: any) => ({
          name: file.name,
          size: file.size,
          path: file.path
        }))
      }));

      setSimulationRuns(transformedRuns);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const toggleRunExpansion = (runId: string) => {
    const newExpanded = new Set(expandedRuns);
    if (newExpanded.has(runId)) {
      newExpanded.delete(runId);
    } else {
      newExpanded.add(runId);
    }
    setExpandedRuns(newExpanded);

    // Mark run as clicked (to remove the bright border)
    setClickedRuns(prev => new Set(prev).add(runId));
  };

  const togglePreview = (fileKey: string, filePath: string) => {
    const newExpanded = new Set(expandedPreviews);
    if (newExpanded.has(fileKey)) {
      newExpanded.delete(fileKey);
    } else {
      newExpanded.add(fileKey);
      // Load preview data if not already loaded
      if (!previewData[fileKey]) {
        loadPreviewData(fileKey, filePath);
      }
    }
    setExpandedPreviews(newExpanded);
  };

  const loadPreviewData = async (fileKey: string, filePath: string) => {
    try {
      // Download the CSV file
      const response = await fetch(`${API_ORIGIN}/api/files/download/${filePath}/`);
      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      const csvText = await response.text();

      // Parse CSV with PapaParse
      Papa.parse(csvText, {
        header: true,
        complete: (results) => {
          // Take only first 10 rows for preview
          const previewRows = results.data.slice(0, 10);
          setPreviewData(prev => ({ ...prev, [fileKey]: previewRows }));
        },
        error: (error: any) => {
          console.error('CSV parsing error:', error);
          setPreviewData(prev => ({
            ...prev,
            [fileKey]: [{ error: 'Failed to parse CSV' }]
          }));
        }
      });
    } catch (error) {
      console.error('Error loading preview:', error);
      setPreviewData(prev => ({
        ...prev,
        [fileKey]: [{ error: 'Failed to load file' }]
      }));
    }
  };

  const handleDownload = (filePath: string, fileName: string) => {
    // Create download link
    const downloadUrl = `${API_ORIGIN}/api/files/download/${filePath}/`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleBulkDownload = (runId: string, runTime: string) => {
    // Create bulk download link
    const downloadUrl = `${API_ORIGIN}/api/files/bulk-download/${runId}/`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `simulation_${runTime.replace(/[^\w\-_\.]/g, '_')}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-16 h-[calc(100vh-4rem)] w-96 bg-background border-l border-border z-40 shadow-xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <File className="h-5 w-5" />
                Generated Files
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 px-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loading ? (
                <div className="text-center text-muted-foreground py-8">
                  <Loader2 className="h-8 w-8 mx-auto mb-4 animate-spin" />
                  <p>Loading files...</p>
                </div>
              ) : error ? (
                <div className="text-center text-muted-foreground py-8">
                  <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-red-500">Error: {error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchSimulationRuns}
                    className="mt-2"
                  >
                    Retry
                  </Button>
                </div>
              ) : simulationRuns.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No simulation files found</p>
                  <p className="text-sm">Run a simulation to generate CSV files</p>
                </div>
              ) : (
                simulationRuns.map((run) => {
                  const isNewRun = !clickedRuns.has(run.id);
                  return (
                    <Card
                      key={run.id}
                      className={`p-4 transition-all duration-300 ${isNewRun
                        ? 'ring-2 ring-orange-300'
                        : ''
                        }`}
                    >
                      {/* Run Header */}
                      <div className="flex items-center justify-between">
                        <button
                          onClick={() => toggleRunExpansion(run.id)}
                          className="flex-1 flex items-center gap-2 text-left hover:text-gray-500 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            {expandedRuns.has(run.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                            <Calendar className="h-4 w-4" />
                            <span className="font-medium">{run.time}</span>
                          </div>
                        </button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleBulkDownload(run.id, run.time)}
                          className="h-8 w-8 px-0 hover:text-orange-300 transition-all duration-200"
                        >
                          <FolderDown className="h-4 w-4" />
                        </Button>
                      </div>

                      {/* Files List */}
                      <AnimatePresence>
                        {expandedRuns.has(run.id) && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-3 space-y-2"
                          >
                            <Separator />
                            {run.files.map((file) => {
                              const fileKey = `${run.id}_${file.name}`;
                              return (
                                <div key={file.name} className="space-y-2">
                                  {/* File Info */}
                                  <div className="flex items-center justify-between p-2 rounded-lg hover:bg-accent/50 transition-colors">
                                    <div className="flex-1 min-w-0">
                                      <p className="font-medium text-sm truncate">
                                        {file.name}.csv
                                      </p>
                                      <p className="text-xs text-muted-foreground">
                                        {file.size}
                                      </p>
                                    </div>
                                    <div className="flex gap-1">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => togglePreview(fileKey, file.path)}
                                        className="h-7 w-7 px-0"
                                      >
                                        <Eye className="h-3 w-3" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleDownload(file.path, `${file.name}.csv`)}
                                        className="h-7 w-7 px-0"
                                      >
                                        <Download className="h-3 w-3" />
                                      </Button>
                                    </div>
                                  </div>

                                  {/* Preview Table */}
                                  <AnimatePresence>
                                    {expandedPreviews.has(fileKey) && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="bg-muted/30 rounded-lg p-3 text-xs"
                                      >
                                        {previewData[fileKey] ? (
                                          previewData[fileKey][0]?.error ? (
                                            <p className="text-red-500 text-center text-xs">
                                              {previewData[fileKey][0].error}
                                            </p>
                                          ) : (
                                            <div className="overflow-x-auto">
                                              <table className="w-full text-xs">
                                                <thead>
                                                  <tr className="border-b border-border">
                                                    {Object.keys(previewData[fileKey][0] || {}).map((header) => (
                                                      <th key={header} className="text-left p-1 font-medium">
                                                        {header}
                                                      </th>
                                                    ))}
                                                  </tr>
                                                </thead>
                                                <tbody>
                                                  {previewData[fileKey].slice(0, 5).map((row, idx) => (
                                                    <tr key={idx} className="border-b border-border/50">
                                                      {Object.values(row).map((value, colIdx) => (
                                                        <td key={colIdx} className="p-1 truncate max-w-20">
                                                          {String(value)}
                                                        </td>
                                                      ))}
                                                    </tr>
                                                  ))}
                                                </tbody>
                                              </table>
                                              <p className="text-muted-foreground mt-2 text-center">
                                                Showing first 5 rows
                                              </p>
                                            </div>
                                          )
                                        ) : (
                                          <div className="flex items-center justify-center py-4">
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                            <p className="text-muted-foreground text-xs">
                                              Loading preview...
                                            </p>
                                          </div>
                                        )}
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              );
                            })}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </Card>
                  );
                })
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
