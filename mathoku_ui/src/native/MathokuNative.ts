import { NativeModules } from 'react-native';

type MathokuNativeType = {
  greet(name: string): Promise<string>;
  getDummyUserJson(): Promise<string>;
};

const { MathokuNative } = NativeModules;

if (!MathokuNative) {
  throw new Error(
    'MathokuNative module is not linked. ' +
    'Did you add MathokuNativePackage() in MainApplication?'
  );
}

export default MathokuNative as MathokuNativeType;