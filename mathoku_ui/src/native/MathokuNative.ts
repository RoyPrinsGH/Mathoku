import { NativeModules } from 'react-native';

type MathokuNativeType = {
  greet(name: string): Promise<string>;
};

// grab our native module by the name you returned in getName()
const { MathokuNative } = NativeModules;

if (!MathokuNative) {
  throw new Error(
    'MathokuNative module is not linked. ' +
    'Did you add MathokuNativePackage() in MainApplication?'
  );
}

export default MathokuNative as MathokuNativeType;