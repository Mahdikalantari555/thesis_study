// Vite's non-JS import suffixes used by the platform data layer.
declare module "*?raw" {
  const content: string;
  export default content;
}
