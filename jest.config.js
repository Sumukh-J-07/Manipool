module.exports = {
  preset: '@react-native/jest-preset',
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|@react-navigation|react-native-screens|react-native-safe-area-context|react-native-svg|lucide-react-native)/)',
  ],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transform: { '^.+\\.(js|jsx|mjs|ts|tsx)$': 'babel-jest' },
};
