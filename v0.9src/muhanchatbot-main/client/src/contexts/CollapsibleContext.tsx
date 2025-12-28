import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

type SetStateAction<S> = (prevState: S) => S;

type CollapsibleContextType = {
  activeIds: Set<string>;
  toggleId: (id: string, isActive: boolean) => void;
  setDefaultExpanded: (id: string, isExpanded: boolean) => void;
};

const CollapsibleContext = createContext<CollapsibleContextType | undefined>(undefined);

export function CollapsibleProvider({ children }: { children: ReactNode }) {
  const [activeIds, setActiveIds] = useState<Set<string>>(new Set());
  const [defaultExpandedMap, setDefaultExpandedMap] = useState<Record<string, boolean>>({});

  // Apply default expanded states after initial render
  useEffect(() => {
    const newActiveIds = new Set<string>();
    
    // Add all IDs that are marked as default expanded
    Object.entries(defaultExpandedMap).forEach(([id, isExpanded]) => {
      if (isExpanded) {
        newActiveIds.add(id);
      }
    });

    setActiveIds(newActiveIds);
  }, [defaultExpandedMap]);

  const toggleId = (id: string, isActive: boolean) => {
    setActiveIds(prevIds => {
      const newIds = new Set(prevIds);
      if (isActive) {
        newIds.delete(id);
      } else {
        newIds.add(id);
      }
      return newIds;
    });
  };

  const setDefaultExpanded = (id: string, isExpanded: boolean) => {
    setDefaultExpandedMap(prev => ({
      ...prev,
      [id]: isExpanded
    }));
  };

  return (
    <CollapsibleContext.Provider value={{ activeIds, toggleId, setDefaultExpanded }}>
      {children}
    </CollapsibleContext.Provider>
  );
}

export function useCollapsible(id: string, defaultExpanded = false) {
  const context = useContext(CollapsibleContext);
  if (!context) {
    throw new Error('useCollapsible must be used within a CollapsibleProvider');
  }

  const { activeIds, toggleId, setDefaultExpanded } = context;
  const isActive = activeIds.has(id);
  
  // Register default expanded state
  useEffect(() => {
    if (defaultExpanded) {
      setDefaultExpanded(id, true);
    }
  }, [id, defaultExpanded, setDefaultExpanded]);

  const toggle = () => {
    toggleId(id, isActive);
  };

  return {
    isActive,
    toggle,
  };
}
