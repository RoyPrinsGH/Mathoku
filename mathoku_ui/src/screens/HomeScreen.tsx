import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';

// Minimal course type definition
interface Course {
  id: string;
  title: string;
}

// Dummy data for now
const courses: Course[] = [
  { id: '1', title: 'Binary Search' },
  { id: '2', title: 'Depth-First Search' },
  { id: '3', title: 'Dijkstra\'s Algorithm' },
];

interface HomeScreenProps {
  navigation: any;
}

export default function HomeScreen({ navigation }: HomeScreenProps) {
  const renderItem = ({ item }: { item: Course }) => (
    <TouchableOpacity
      style={styles.item}
      onPress={() => navigation.navigate('CourseDetail', { courseId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={courses}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  item: { padding: 12, marginBottom: 8, backgroundColor: '#eee', borderRadius: 4 },
  title: { fontSize: 18 },
});
