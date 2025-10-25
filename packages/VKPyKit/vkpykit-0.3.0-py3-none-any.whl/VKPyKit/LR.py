import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score,  accuracy_score, recall_score, precision_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score


from IPython.display import display
# to split the data into train and test sets
from sklearn.model_selection import train_test_split

# to build a linear regression model
from sklearn.linear_model import LinearRegression


class LR:

    def __init__(self):
        pass

    """
    To plot simple LR visualizations
    """
    # function to compute MAPE
    def mape_score(self, targets, predictions):
        return np.mean(np.abs(targets - predictions) / targets) * 100

    # function to compute adjusted R-squared
    def adj_r2_score(self, predictors, targets, predictions):
        r2 = r2_score(targets, predictions)
        n = predictors.shape[0]
        k = predictors.shape[1]
        return 1 - ((1 - r2) * (n - 1) / (n - k - 1))

    # function to compute different metrics to check performance of a regression model
    def model_performance_regression(self, model, predictors, target):
        """
        Function to compute different metrics to check regression model performance

        model: regression model
        predictors: independent variables
        target: dependent variable
    
        RMSE (Root Mean Squared Error): 
            RMSE measures the square root of the average squared differences between actual 
            and predicted values, providing a metric that is in the same units as the target 
            variable and penalizes larger errors more heavily.
        MAPE (Mean Absolute Percentage Error): 
            MAPE calculates the average absolute percentage difference between actual and 
            predicted values, expressing prediction accuracy as a percentage and allowing 
            for easy interpretation across different scales.
        R² (Coefficient of Determination): 
            R² indicates the proportion of the variance in 
            the dependent variable that is predictable from the independent variables, with 
            values closer to 1 signifying a better fit.
        MAE (Mean Absolute Error): 
            MAE measures the average absolute difference between the actual and predicted 
            values, providing a straightforward metric of prediction accuracy.
        """

        # predicting using the independent variables
        pred = model.predict(predictors)

        rmse = np.sqrt(mean_squared_error(target, pred))  # to compute RMSE
        mae = mean_absolute_error(target, pred)  # to compute MAE
        mape = self.mape_score(target, pred)  # to compute MAPE
        r2 = r2_score(target, pred)  # to compute R-squared
        adj_r2 = self.adj_r2_score(predictors, target, pred)  # to compute Adjusted R-squared

        # creating a dataframe of metrics
        df_perf = pd.DataFrame(
            {
                "RMSE": rmse,
                "MAE": mae,
                "MAPE": mape,
                "R-squared": r2,
                "Adj R-squared": adj_r2,
            },
            index=[0],
        )

        return df_perf