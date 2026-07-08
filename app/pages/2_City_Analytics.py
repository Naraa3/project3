'''# Table
st.subheader("Results")

table_df = filtered_df.copy()

table_df["address"] = table_df["address"].fillna("—")

table_df = table_df.rename(columns={
    "name": "Name",
    "category": "Category",
    "address": "Address",
    "city": "City"
})

st.dataframe(
    table_df[["Name", "Category", "Address", "City"]],
    use_container_width=True
)'''