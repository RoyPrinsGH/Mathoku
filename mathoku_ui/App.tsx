import React, { useState } from 'react';
import { SafeAreaView, Button, Text, StyleSheet } from 'react-native';
import MathokuNative from './src/native/MathokuNative';

export default function App() {
  const [message, setMessage] = useState<string>('no message yet');

  const onPress = async () => {
    try {
      const numCalls = 1000;
      const startTime = performance.now();
      for (let i = 0; i < numCalls; i++) {
        await MathokuNative.greet('React User');
      }
      const endTime = performance.now();
      const duration = endTime - startTime;
      const averageTime = duration / numCalls;
      setMessage(
        `Made ${numCalls} calls in ${duration.toFixed(3)} ms.\n` +
        `Average time per call: ${averageTime.toFixed(3)} ms.`
      );
    } catch (err: any) {
      console.error(err);
      setMessage('Error: ' + (err.message || JSON.stringify(err)));
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Button title="Say Hello from Rust!" onPress={onPress} />
      <Text style={styles.text}>{message}</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { marginTop: 20, fontSize: 18 },
});