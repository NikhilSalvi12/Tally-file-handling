import pandas as pd
import xml.etree.ElementTree as ET

# defining the child type
child = ["Agst Ref","New Ref"]


def parsing_xml(filename):
    # Data frame for final result
    DF = pd.DataFrame(columns=["Date", "Transaction Type", "Vch No.", "Ref No", "Ref Type", "Ref Date", "Debtor",
                               "Ref Amount", "Amount", "Particulars", "Vch Type", "Amount Verified"])

    user_input = ET.parse(filename)

    body = user_input.find("BODY") #finding the main content
    for i in list(body):
        Request_data = i.find("REQUESTDATA") #tally stores all data in Requestdata

    for data in list(Request_data):
        for voucher in list(data):
            # seperating the transactions listed as receipt, can be made dynamic to find other entries
            if voucher.get("VCHTYPE") == "Receipt":
                #skeleton for the DF
                entry = {"Date": None, "Transaction Type": None, "Vch No.": None, "Ref No": None, "Ref Type": None,
                         "Ref Date": None, "Debtor": None, "Ref Amount": None, "Amount": None,
                         "Particulars": None, "Vch Type": "Receipt", "Amount Verified": None}
                for elements in list(voucher):
                    if elements.tag == "DATE":
                        entry["Date"] = elements.text
                    elif elements.tag == "REFERENCEDATE":
                        entry["Ref Date"] = elements.text
                    elif elements.tag == "VOUCHERNUMBER":
                        entry["Vch No."] = elements.text
                    elif elements.tag == "ALLLEDGERENTRIES.LIST":
                        for entries in list(elements):
                            if entries.tag == "LEDGERNAME":
                                entry["Debtor"] = entry["Particulars"] = entries.text
                            elif entries.tag == "AMOUNT":
                                entry["Amount"] = entries.text

                                # classifying the parent transaction type
                                if "Bank" not in entry["Debtor"]:
                                    entry["Ref No"] = entry["Ref Type"] = entry["Ref Date"] = entry["Ref Amount"] = "NA"
                                    entry["Transaction Type"] = "Parent"
                                    DF = DF.append(entry, ignore_index=True)
                            elif entries.tag == "BILLALLOCATIONS.LIST":
                                for bills in list(entries):
                                    if bills.tag == "NAME":
                                        entry["Ref No"] = bills.text
                                    elif bills.tag == "BILLTYPE":
                                        entry["Ref Type"] = bills.text
                                    elif bills.tag == "AMOUNT":
                                        entry["Ref Amount"] = bills.text

                                #seperating the Bank and child transaction type
                                if "Bank" in entry["Debtor"]:
                                    entry["Ref No"] = entry["Ref Type"] = entry["Ref Date"] = entry["Ref Amount"] = "NA"
                                    entry["Transaction Type"] = "Other"
                                    DF = DF.append(entry, ignore_index=True)
                                elif entry["Ref Type"] in child:
                                    entry["Amount"] = "NA"
                                    entry["Transaction Type"] = "Child"
                                    entry["Ref Date"] = None if entry["Ref Date"] == "NA" else entry["Ref Date"]
                                    DF = DF.append(entry,ignore_index=True)
    return DF #returning the result


def creating_dataframe(DF):
    DF.Date = pd.to_datetime(DF.Date).dt.strftime('%d-%m-%Y')
    DF.to_csv("sample.csv", index=False)
    DF = pd.read_csv("sample.csv")
    temp_DF = DF.drop(DF.loc[DF["Transaction Type"] == "Other"].index)
    group = temp_DF.groupby(["Vch No."]).aggregate({"Amount": 'sum', "Ref Amount": 'sum'})

    group.reset_index(inplace=True)

    group["Valid"] = group.Amount == group["Ref Amount"]

    group.drop(columns=["Amount","Ref Amount"],inplace = True)

    group["Transaction Type"] = "Parent"

    temp_DF = DF.copy()

    temp_DF = pd.merge(temp_DF, group, how="left", on=["Vch No.","Transaction Type"])

    DF["Amount Verified"] = temp_DF.Valid.copy()

    DF.loc[DF["Amount Verified"] == True,"Amount Verified"] = "Yes"
    DF.loc[DF["Amount Verified"] == False,"Amount Verified"] = "No"
    DF.loc[(DF["Transaction Type"] == "Child") | (DF["Transaction Type"] == "Other"), "Amount Verified" ] = "NA"
    DF.loc[(DF["Transaction Type"] == "Parent") | (DF["Transaction Type"] == "Other"),["Ref No","Ref Type","Ref Date","Ref Amount"]] = "NA"
    DF.loc[DF["Transaction Type"] == "Child","Amount"] = "NA"
    DF.to_excel("Response.xlsx", index=False)


filename = "Input.xml"
DF = parsing_xml(filename)
creating_dataframe(DF)
