def getutil5():
    return """
        import tensorflow as tf
        from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
        import numpy as np
        import matplotlib.pyplot as plt
        import os


        # In[2]:


        model_path = r"..\_Transfer_Learning_Freshwater_Fish_Disease.hdf5"
        test_dir = r"..\Freshwater Fish Disease Aquaculture in south asia\Test"

        # In[3]:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully")


        # In[4]:
        class_names = [
            'Bacterial diseases - Aeromoniasis',
            'Bacterial gill disease',
            'Bacterial Red disease',
            'Fungal diseases Saprolegniasis',
            'Healthy Fish',
            'Parasitic diseases',
            'Viral diseases White tail disease'
        ]


        # In[5]:
        datagen = ImageDataGenerator(rescale=1./255)
        test_gen = datagen.flow_from_directory(
            test_dir,
            target_size=(224, 224),
            batch_size=1,
            class_mode='categorical',
            shuffle=False
        )


        # In[6]:
        predictions = model.predict(test_gen, verbose=1)
        predicted_classes = np.argmax(predictions, axis=1)


        # In[7]:
        from sklearn.metrics import confusion_matrix, classification_report
        import seaborn as sns


        # In[8]:
        true_classes = test_gen.classes
        cm = confusion_matrix(true_classes, predicted_classes)


        # In[9]:
        plt.figure(figsize=(8,6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.show()


        # In[10]:
        print("\nClassification Report:\n")
        print(classification_report(true_classes, predicted_classes, target_names=class_names))
        """